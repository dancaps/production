import requests
import boto3
import json
from time import sleep

# variables
friendly_name = ''
aws_access_key = ''
aws_secret_key = ''
cc_api_key = ''
cc_api_url = 'https://api.cloudcheckr.com/api/account.json/{0}'

def main():
    # this is where the magic happens

    global cc_api_key
    global aws_access_key
    global aws_secret_key
    global friendly_name
    global aws_assume_role_policy
    global cc_api_url

    # user information gathering
    if len(cc_api_key) < 1:
         cc_api_key = raw_input('What is your cloudcheckr API key?')
    if len(aws_access_key) < 1:
        aws_access_key = raw_input('What is your aws access key?')
        aws_secret_key = raw_input('What is your aws secret key?')
    if len(friendly_name) < 1:
        friendly_name = raw_input('What is the friendly name of the account you want to create?')

    print('The user information has been gathered')

    # retrieves a dictionary filled with aws account information
    aws_information = get_aws_information(aws_access_key, aws_secret_key)

    print('The aws account information has been retrieved.')

    # checking to see if the cloudcheckr account name already exists
    if cc_account_id_check(cc_api_key, aws_information['account']):
        print("An account with this id already exists. Please try again.")
        exit()

    print('There is no account with the same account number in Cloudcheckr.')

    # get cloudcheckr policy json
    cc_policy = requests.get('https://s3.amazonaws.com/checkr3/CC_IAM_FullPolicy.json').json()

    print('The cloudcheckr json policy has been downloaded from the web.')
    
    # creating the cloudcheckr account and getting the account id and external id returned
    cc_account = create_new_cc_account(cc_api_key, cc_api_url, friendly_name)

    print('The cloudcheckr account has been created')

    # building the aws role policy based on the information returned when creating the cloudcheckr account.
    aws_assume_role_policy = {"Version": "2012-10-17",
                          "Statement": {"Effect": "Allow",
                                        "Action": "sts:AssumeRole",
                                        "Principal": {"AWS": cc_account['role_account_id']},
                                        "Condition": {"StringEquals": {"sts:ExternalId": cc_account['cc_external_id']}}}}

    print('The account to account aws role policy has been created.')

    # send the cc policy and roles to aws to create the policy
    aws_requirements = create_aws_requirements(aws_assume_role_policy, aws_access_key, aws_secret_key, cc_policy)

    print('The policy and role in aws has been created and linked to cloudcheckr')

    # this gives cloudcheckr time to initialize the account before adding the arn. Without this you get an error.
    sleep(20)
    
    print('Im awake again. Starting the funcion')
    
    # add the role arn to the cloudcheckr account
    add_aws_arn_to_cc_account(cc_api_key, cc_api_url, aws_requirements['role_arn'], friendly_name)

    print('The cloudcheckr account was linked back to the aws account.')
    print('The inital cloudcheckr scan has started. Have a nice day!!!')


def cc_account_id_check(cc_api_key, aws_account_id):
    # checks cloudcheckr to see if the aws account id already exists. Returns True or False

    # api call
    data = requests.get('https://api.cloudcheckr.com/api/account.json/get_accounts_v2?access_key=' + cc_api_key).json()

    # searching for the account name, returns True if found
    for i in data['accounts_and_users']:
        if aws_account_id == i['aws_account_id']:
            return True

    return False


def get_aws_information(aws_access_key, aws_secret_key):
    # gets the account number from the aws account. Returns the account number

    return_payload = {}

    # login to sts
    client = boto3.client('sts', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

    #get account id
    return_payload['account'] = client.get_caller_identity().get('Account')

    return return_payload


def create_aws_requirements(aws_assume_role_policy, aws_access_key, aws_secret_key, cc_policy):
    # creates the cloudcheckr policy, role and attaches them. Returns the role arn.

    return_payload = {}

    # login to sts
    client = boto3.client('iam', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

    # creating the policy
    try:
        policy_response = client.create_policy(PolicyName='CloudCheckrPolicy', PolicyDocument=json.dumps(cc_policy))
    except:
        print('A cloudcheckr policy already exists with that name. Please try again.')
        exit()

    # checking if the policy was created successfully
    if policy_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        exit()

    # creating the role
    try:
        role_response = client.create_role(RoleName='CloudCheckrRole',
                                           AssumeRolePolicyDocument=json.dumps(aws_assume_role_policy))
    except:
        print('A cloudcheckr role already exists with that name. Please try again.')
        exit()

    # checking if the role was created successfully
    if role_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        exit()

    # attaching the policy to the role
    try:
        attach_policy_response = client.attach_role_policy(RoleName='CloudCheckrRole',
                                                           PolicyArn=policy_response['Policy']['Arn'])
    except:
        print('There was a problem attaching the policy to the role. Please try again.')
        exit()

    # checking if the policy and role attached properly
    if attach_policy_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        exit()

    # building the return json file
    return_payload['role_arn'] = role_response['Role']['Arn']

    return return_payload


def create_new_cc_account(cc_api_key, cc_api_url, friendly_name):
    # creates the cloudcheckr account. Returns the entire json

    url = cc_api_url.format('add_account_v3').strip()
    headers = {'Content-Type': 'application/json', 'access_key': cc_api_key}
    data = {'account_name': friendly_name}

    # creating the account
    r = requests.post(url, headers=headers, data=json.dumps(data))

    # verifying the account created successfully
    if r.status_code != 200:
        print('There was a problem creating the cloudcheckr account. Please try again.')
        exit()

    return r.json()


def add_aws_arn_to_cc_account(cc_api_key, cc_api_url, aws_role_arn, friendly_name):
    # adds the arn to the cloudcheckr account. Returns the entire json

    url = cc_api_url.format('edit_credential').strip()
    headers = {'Content-Type': 'application/json', 'access_key': cc_api_key}
    data = {'use_account': friendly_name, 'aws_role_arn': aws_role_arn}

    # adding the arn to the cloudcheckr account
    r = requests.post(url, headers=headers, data=json.dumps(data))

    # checking to make sure the arn was added successfully
    if r.status_code != 200:
        print('There was a problem adding the aws role arn to the cloudcheckr account. Please try again.')
        exit()

    return r.json()


if __name__ == '__main__':
    main()
