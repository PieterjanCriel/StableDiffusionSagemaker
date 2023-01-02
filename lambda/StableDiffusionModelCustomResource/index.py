import os
import sagemaker

from crhelper import CfnResource
import logging

from sagemaker import image_uris, model_uris, script_uris
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.utils import name_from_base


logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level='DEBUG',
                     boto_level='CRITICAL', sleep_on_delete=120, ssl_verify=None)

try:
    sess = sagemaker.Session()
    # sagemaker session bucket -> used for uploading data, models and logs
    # sagemaker will automatically create this bucket if it not exists
    sagemaker_session_bucket = None
    if sagemaker_session_bucket is None and sess is not None:
        # set to default bucket if a bucket name is not given
        sagemaker_session_bucket = sess.default_bucket()
    role = os.environ['sageMakerRoleArn']
    sess = sagemaker.Session(default_bucket=sagemaker_session_bucket)

    print(f"sagemaker role arn: {role}")
    print(f"sagemaker bucket: {sess.default_bucket()}")
    print(f"sagemaker session region: {sess.boto_region_name}")
    pass
except Exception as e:
    helper.init_failure(e)


def handler(event, context):
    print(event)
    helper(event, context)


@helper.create
def create(event, context):
    logger.info("Got Create")

    model_id = os.environ['ModelId']
    model_version = os.environ['ModelVersion']
    endpoint_name = "stablediffusion-d2"

    # Please use ml.g5.24xlarge instance type if it is available in your region. ml.g5.24xlarge has 24GB GPU compared to 16GB in ml.p3.2xlarge and supports generation of larger and better quality images.
    inference_instance_type = os.environ['inferenceInstancetype']
    logger.info(f"Using a {inference_instance_type} type for inference")

    # Retrieve the inference docker container uri. This is the base HuggingFace container image for the default model above.
    deploy_image_uri = image_uris.retrieve(
        region=None,
        framework=None,
        image_scope="inference",
        model_id=os.environ['ModelId'],
        model_version=model_version,
        instance_type=inference_instance_type,
    )

    logger.info(f"Deploy image uri {deploy_image_uri}")

    # Retrieve the inference script uri. This includes all dependencies and scripts for model loading, inference handling etc.
    deploy_source_uri = script_uris.retrieve(
        model_id=model_id, model_version=model_version, script_scope="inference"
    )

    # Retrieve the model uri. This includes the pre-trained nvidia-ssd model and parameters.
    model_uri = model_uris.retrieve(
        model_id=model_id, model_version=model_version, model_scope="inference"
    )

    logger.info(f"Model uri {model_uri}")

    # To increase the maximum response size from the endpoint.
    env = {
        "MMS_MAX_RESPONSE_SIZE": "20000000",
    }

    # Create the SageMaker model instance
    model = Model(
        image_uri=deploy_image_uri,
        source_dir=deploy_source_uri,
        model_data=model_uri,
        entry_point="inference.py", # entry point file in source_dir and present in deploy_source_uri
        role=role,
        predictor_cls=Predictor,
        name=endpoint_name,
        env=env,
    )

    # deploy the Model. Note that we need to pass Predictor class when we deploy model through Model class,
    # for being able to run inference through the sagemaker API.
    logger.info(f"Model deploy start")
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=inference_instance_type,
        predictor_cls=Predictor,
        endpoint_name=endpoint_name,
    )
    logger.info(f"Model deploy end")

    print(predictor.endpoint_name)
    helper.Data['endpoint_name'] = predictor.endpoint_name
    return predictor.endpoint_name


@helper.delete
def delete(event, context):
    logger.info("Got Delete")
    physical_id = event["PhysicalResourceId"]
    predictor = Predictor(
        endpoint_name=physical_id, sagemaker_session=sess)
    predictor.delete_model()
    predictor.delete_endpoint()


@helper.update
def update(event, context):
    logger.info("Got Update")
    delete(event, context)
    return create(event, context)