"""serializeImageData Lambda Function"""
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

"""myClassificationFunction Lambda Function"""
import json
import boto3
import base64

runtime = boto3.Session().client('sagemaker-runtime')

# Fill this in with the name of your deployed model
ENDPOINT = 'image-classification-2024-03-29-18-32-00-791'

def lambda_handler(event, context):

    # Decode the image data
    image_data = base64.b64decode(event['body']['image_data'])

    # Instantiate a Predictor
    predictor = runtime.invoke_endpoint(EndpointName=ENDPOINT, ContentType = 'image/png',Body = image_data) # event['body']['image_data'])

    # For this model the IdentitySerializer needs to be "image/png"
    # predictor.serializer = IdentitySerializer("image/png")

    # Make a prediction:
    # inferences = predictor.predict(image)
    inferences = json.loads(predictor['Body'].read())
    # We return the data back to the Step Function    
    event["inferences"] = inferences
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

"""myThresholdFunction Lambda Function"""

import json

THRESHOLD = .70

def lambda_handler(event, context):
    body = json.loads(event['body'])
    inferences = body["inferences"]

    meets_threshold = any(score > THRESHOLD for score in inferences)

    if meets_threshold:
        pass
    else:
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
