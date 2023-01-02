import path = require('path');
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { LayerVersion, Runtime } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { BlockPublicAccess, Bucket } from 'aws-cdk-lib/aws-s3';
import { Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { StableDiffusionInferenceConstruct } from './constructs/StableDiffusionInferenceConstruct';

type StableDiffusionStackProps = StackProps;

export class StableDiffusionStack extends Stack {
    public stackMessage: string;

    constructor(scope: Construct, id: string, props: StableDiffusionStackProps) {
        super(scope, id, props);

        const sdConstruct = new StableDiffusionInferenceConstruct(this, 'StableDiffusionInferenceConstructConstruct', {
            modelId: 'model-txt2img-stabilityai-stable-diffusion-v2-fp16',
            modelVersion: '*',
        });

        const lambdaRole = new Role(this, 'Role', {
            assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
        });

        const outputBucket = new Bucket(this, 'StableDiffusionOutput', {
            blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
        });

        outputBucket.grantReadWrite(lambdaRole);

        new PythonFunction(this, 'StableDiffusionFunction', {
            runtime: Runtime.PYTHON_3_9,
            memorySize: 512,
            description: 'Stable diffusion lambda function',
            timeout: Duration.seconds(30),
            index: 'index.py',
            handler: 'lambda_handler',
            role: lambdaRole,
            entry: path.join(__dirname, '..', 'lambda', 'StableDiffusionModelFunction'),
            environment: {
                endpointName: sdConstruct.endpointName,
                outputBucket: outputBucket.bucketName,
            },
            layers: [
                LayerVersion.fromLayerVersionArn(
                    this,
                    'PillowLayer',
                    'arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p39-pillow:1'
                ),
            ],
            initialPolicy: [sdConstruct.invokeEndPointPolicyStatement],
        });
    }
}
