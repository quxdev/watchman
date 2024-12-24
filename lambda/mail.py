import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from boto3 import client as aws_client


class AWSEmail:
    def __init__(self):
        self.sender = "qux@quxdev.com"
        self.to = None
        self.cc = None
        self.bcc = None
        self.subject = None
        self.message = None
        self.files = None
        self.client = self.set_client()

    def set_client(self):
        access_key = os.getenv("SES_ACCESS_KEY", None)
        secret_key = os.getenv("SES_SECRET_KEY", None)
        aws_region = os.getenv("SES_REGION", "us-east-1")

        client = aws_client(
            service_name="ses",
            region_name=aws_region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        return client

    @staticmethod
    def destination_header(value):
        result = value
        if isinstance(value, list):
            stripped_value = [x.strip() for x in value]
            result = ",".join(stripped_value)
        return result

    @staticmethod
    def destination_aslist(*args):
        result = []
        for arg in args:
            if isinstance(arg, str):
                new_args = arg.split(",")
                result.extend(new_args)
            elif isinstance(arg, list):
                result.extend(arg)

        return result

    @staticmethod
    def getattachment(filepath):
        if not os.path.exists(filepath):
            return None

        with open(filepath, "rb") as f:
            filedata = f.read()
            filename = os.path.basename(filepath)
            part = MIMEApplication(filedata, filename)
        part.add_header("Content-Disposition", "attachment", filename=filename)
        return part

    def send(self):
        if not any([self.client, self.subject, self.message, self.to]):
            print("Missing one or more of the following: client, subject, message, to")
            print(f"client : {self.client}")
            print(f"subject: {self.subject}")
            print(f"message: {self.message}")
            print(f"to     : {self.to}")

            return False

        message = MIMEMultipart()

        message["Subject"] = self.subject
        message["From"] = self.sender

        to, cc, bcc = self.set_receipients(self.to, self.cc, self.bcc)

        message["To"] = to
        message["Cc"] = cc
        message["Bcc"] = bcc

        if not message["To"]:
            print(f"Missing To: {message['To']}")
            return False

        part = MIMEText(self.message, "html", "utf-8")
        message.attach(part)

        if self.files:
            if not isinstance(self.files, list):
                self.files = [self.files]

            for file in self.files:
                attachment = self.getattachment(file)
                if attachment:
                    message.attach(attachment)
                else:
                    print(f"Cannot attach file:{file}")

        rawmessage = {"Data": message.as_string()}

        response = self.client.send_raw_email(
            Destinations=self.destination_aslist(to, cc, bcc),
            Source=self.sender,
            RawMessage=rawmessage,
        )

        if (
            response
            and response["ResponseMetadata"]
            and response["ResponseMetadata"]["HTTPStatusCode"] != 200
        ):
            print(
                f"Failed to send email: status={response['ResponseMetadata']['HTTPStatusCode']}"
            )
            return False

        return True

    def set_receipients(self, to, cc, bcc):

        recepient_to = None
        recepient_cc = None
        recepient_bcc = None

        recepient_to = self.destination_header(to)
        recepient_cc = self.destination_header(cc)
        recepient_bcc = self.destination_header(bcc)

        print(f"recepient_to: {recepient_to}")
        print(f"recepient_cc: {recepient_cc}")
        print(f"recepient_bcc: {recepient_bcc}")

        return recepient_to, recepient_cc, recepient_bcc
