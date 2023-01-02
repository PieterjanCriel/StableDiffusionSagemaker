import * as path from 'path';
import { Construct } from 'constructs';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Duration, CustomResource, RemovalPolicy, Stack, Size } from 'aws-cdk-lib';
import { Runtime } from 'aws-cdk-lib/aws-lambda';
import { Role, ServicePrincipal, ManagedPolicy, PolicyStatement } from 'aws-cdk-lib/aws-iam';

export interface StableDiffusionInferenceConstructProps {
    modelId: string;
    modelVersion?: string;
    inferenceInstancetype?: string;
}

export class StableDiffusionInferenceConstruct extends Construct {
    public readonly endpointName: string;
    public readonly invokeEndPointPolicyStatement: PolicyStatement;
    constructor(scope: Construct, id: string, props: StableDiffusionInferenceConstructProps) {
        super(scope, id);

        const sageMakerRole = new Role(this, 'Role', {
            assumedBy: new ServicePrincipal('sagemaker.amazonaws.com'),
        });
        sageMakerRole.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'));

        const customResourceFunction = new PythonFunction(this, 'customerResourceFunction', {
            index: 'index.py',
            handler: 'handler',
            runtime: Runtime.PYTHON_3_9,
            memorySize: 10240,
            ephemeralStorageSize: Size.gibibytes(10),
            description: 'StableDiffusionModelCustomResource',
            entry: path.join(__dirname, '..', '..', 'lambda', 'StableDiffusionModelCustomResource'),
            environment: {
                ModelId: props.modelId,
                ModelVersion: props.modelVersion || '*', // * will fetch the latest model
                inferenceInstancetype: props.inferenceInstancetype || 'ml.p3.2xlarge',
                sageMakerRoleArn: sageMakerRole.roleArn,
            },
            timeout: Duration.minutes(15),
        });

        customResourceFunction.role?.grantPassRole(sageMakerRole);
        customResourceFunction.role?.addManagedPolicy(
            ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess')
        );

        const huggingFaceModelSagemakerServerlessInferenceCustomResource = new CustomResource(this, 'sdmodel', {
            serviceToken: customResourceFunction.functionArn,
            removalPolicy: RemovalPolicy.DESTROY,
        });
        this.endpointName = huggingFaceModelSagemakerServerlessInferenceCustomResource.getAttString('endpoint_name');

        this.invokeEndPointPolicyStatement = new PolicyStatement({
            actions: ['sagemaker:InvokeEndpoint'],
            resources: [
                `arn:aws:sagemaker:${Stack.of(this).region}:${Stack.of(this).account}:endpoint/${this.endpointName}`,
            ],
        });
    }
}
