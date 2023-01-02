#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { StableDiffusionStack } from '../lib/StableDiffusionStack';

const app = new cdk.App();

new StableDiffusionStack(app, 'StableDiffusionStack', {});
