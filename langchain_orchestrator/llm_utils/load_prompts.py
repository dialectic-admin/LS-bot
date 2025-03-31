import boto3
import importlib.util
import sys

def load_prompts_from_s3(bucket_name, key, module_name="snippet_prompts"):
    """
    
    Download the Python module from s3 and import direcly into memory
    
    
    Args:
        bucket_name: The name of the bucket
        key: The key of the object
        module_name: The name of the module

    Returns:
        The module
    """

    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    content = response['Body'].read()
    
    spec = importlib.util.spec_from_loader(
        module_name,
        loader=importlib.machinery.SourceFileLoader(module_name, key)
    )

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(content, module.__dict__)
    return module

def main():
    prompts_module = load_prompts_from_s3(
        "llm-aihub-prompts",
        "snippet_prompts.py"
    )
    return prompts_module