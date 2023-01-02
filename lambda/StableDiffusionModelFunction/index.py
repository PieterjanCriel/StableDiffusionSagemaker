import os
import sagemaker
import json
import boto3
from botocore.exceptions import ClientError
from PIL import Image
import numpy as np
import logging
import uuid

from sagemaker import Predictor

sess = sagemaker.Session()

output_bucket = os.environ['outputBucket']
s3_client = boto3.client('s3')

def inference(prompt):
    predictor = Predictor(
        endpoint_name=os.environ['endpointName'], sagemaker_session=sess)

    response = predictor.predict(
        prompt.encode("utf-8"),
        {
            "ContentType": "application/x-text",
            "Accept": "application/json",
        },
    )
    return response

def lambda_handler(event, context):
    prompt = ""
    if 'prompt' in event:
        prompt = event['prompt']
    elif 'httpMethod' in event:
        if event['httpMethod'] == 'POST':
            #base64 to prompt
            print(event['body'])
            body = event['body']
            try:
                prompt = json.loads(body)['prompt']
            except:
                return {
                    'statusCode': 400,
                    'body': json.dumps('No prompt specified')
                }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('No prompt specified')
        }
    
    res = inference(prompt)
    
    response_dict = json.loads(res)
    im = Image.fromarray(np.array((response_dict['generated_image'])).astype(np.uint8), 'RGB')
    im.save("/tmp/image.png")

    output_name = f"{uuid.uuid4()}.png"

    try:
        response = s3_client.upload_file('/tmp/image.png', output_bucket, output_name)
        # create presigned url
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': output_bucket, 'Key': output_name},
            ExpiresIn=3600
        )

    except ClientError as e:
        logging.error(e)
        return False

    return {
        "statusCode": 200,
        "body": json.dumps({
            "url": presigned_url,
            "prompt": prompt
        })

    }
