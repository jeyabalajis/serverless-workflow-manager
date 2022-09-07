import base64

import boto3
from botocore.exceptions import ClientError

from exceptions.workflow_run_time_error import WorkflowRunTimeError
from services.config.env_util import EnvUtil
from services.secrets.abstract_secrets_manager import SecretsManager


class AwsSecretsManager(SecretsManager):
    SERVICE_NAME = 'secretsmanager'

    def __init__(self, *, profile_name: str = None, region: str = "ap-south-1"):
        super().__init__(profile_name=profile_name, region=region)
        self.client = None
        self.__init_client_session()

    def __init_client_session(self):
        if self.profile_name is not None:
            aws_profile_name = self.profile_name
        else:
            aws_profile_name = EnvUtil.get_aws_profile_name()

        print("aws profile name: {}".format(aws_profile_name))

        if aws_profile_name is None:
            session = boto3.session.Session()
        else:
            session = boto3.session.Session(profile_name=aws_profile_name)

        self.client = session.client(
            service_name=self.SERVICE_NAME,
            region_name=self.region
        )

    def get_secret(self, *, secret_name: str):
        super(AwsSecretsManager, self).get_secret(secret_name=secret_name)
        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            import traceback
            raise WorkflowRunTimeError(traceback.format_exc(e))
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                return secret
            else:
                decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
                return decoded_binary_secret
