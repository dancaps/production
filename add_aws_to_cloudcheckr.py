import requests
import boto3
import json
from pprint import pprint

# variables
cc_api_key = ''
aws_access_key = ''
aws_secret_key = ''
friendly_name = ''
cc_account_id = ''
cc_external_id = ''
aws_assume_role_policy = {"Version": "2012-10-17",
                              "Statement": {
                                           "Effect": "Allow",
                                           "Action": "sts:AssumeRole",
                                           "Principal": {"AWS": cc_account_id},
                                           "Condition": {"StringEquals": {"sts:ExternalId": cc_external_id}}}}

def main():
    # this is where the magic happens

    global cc_api_key
    global aws_access_key
    global aws_secret_key
    global friendly_name
    global cc_account_id
    global cc_external_id
    global aws_assume_role_policy

    # information gathering
    if len(cc_api_key) < 1:
         cc_api_key = raw_input('What is your cloudcheckr API key?')
    if len(aws_access_key) < 1:
        aws_access_key = raw_input('What is your aws access key?')
        aws_secret_key = raw_input('What is your aws secret key?')
    if len(friendly_name) < 1:
        friendly_name = raw_input('What is the friendly name of the account you want to create?')

    # retrieves a dictionary filled with aws account information
    aws_information = get_aws_information(aws_access_key, aws_secret_key)

    # checking to see if the cloudcheckr account name already exists
    if cc_account_id_check(cc_api_key, aws_information['account']):
        print("An account with this id already exists. Please try again.")
        exit()

    # get cloudcheckr policy json
    cc_policy = requests.get('https://s3.amazonaws.com/checkr3/CC_IAM_FullPolicy.json').json()

    # send the cc policy and roles to aws to create the policy
    print(create_aws_requirements(aws_assume_role_policy, aws_access_key, aws_secret_key, cc_policy))


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
        role_response = client.create_role(RoleName='CloudCheckrRole', AssumeRolePolicyDocument=json.dumps(aws_assume_role_policy))
    except:
        print('A cloudcheckr role already exists with that name. Please try again.')
        exit()

    # checking if the role was created successfully
    if role_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        exit()

    # attaching the policy to the role
    try:
        attach_policy_response = client.attach_role_policy(RoleName='CloudCheckrRole', PolicyArn=policy_response['Policy']['Arn'])
    except:
        print('There was a problem attaching the policy to the role. Please try again.')
        exit()

    # checking if the policy and role attached properly
    if attach_policy_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        exit()

    # building the return json file
    return_payload['role_arn'] = role_response['Role']['Arn']

    return return_payload


def create_new_cc_account():
    pass


if __name__ == '__main__':
    main()
