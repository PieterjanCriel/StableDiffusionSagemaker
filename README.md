### The Stable Diffusion Stack

The `StableDiffusionStack` deploys a `stabilityai-infer/infer-model-txt2img-stabilityai-stable-diffusion-v2-fp16.tar.gz` stable difussion model (text2image).

It is deployed on a sagemaker endpoint using a `ml.p3.2xlarge` instance.

```json
{
  "prompt": "a cat on a skateboard"
}
```

It will return the prompt and will generate an image that is uploaded to an S3 bucket (see in the Stack)

