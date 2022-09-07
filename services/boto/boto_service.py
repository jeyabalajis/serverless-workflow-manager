import boto3


class BotoService:
    SQS_SERVICE_NAME = "sqs"

    def __init__(self, *, profile_name: str, region_name: str, service_name: str):
        self.profile_name = profile_name
        self.region_name = region_name
        self.service_name = service_name

    def get_client(self):
        if self.profile_name is None:
            session = boto3.session.Session()
        else:
            session = boto3.session.Session(profile_name=self.profile_name)

        return session.resource(service_name=self.service_name, region_name=self.region_name)
