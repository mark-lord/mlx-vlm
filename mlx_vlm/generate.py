import argparse
import codecs

import mlx.core as mx

from .prompt_utils import get_message_json
from .utils import generate, get_model_path, load, load_config, load_image_processor

DEFAULT_MODEL_PATH = "mlx-community/nanoLLaVA-1.5-4bit"
DEFAULT_IMAGE = ("http://images.cocodataset.org/val2017/000000039769.jpg",)
DEFAULT_PROMPT = "What are these?"
DEFAULT_MAX_TOKENS = 100
DEFAULT_TEMP = 0.3
DEFAULT_TOP_P = 1.0
DEFAULT_SEED = 0


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate text from an image using a model."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="The path to the local model directory or Hugging Face repo.",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=DEFAULT_IMAGE,
        help="URL or path of the image to process.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        help="Message to be processed by the model.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum number of tokens to generate.",
    )
    parser.add_argument(
        "--temp", type=float, default=DEFAULT_TEMP, help="Temperature for sampling."
    )
    parser.add_argument("--verbose", action="store_false", help="Detailed output.")
    return parser.parse_args()


def get_model_and_processors(model_path):
    model_path = get_model_path(model_path)
    config = load_config(model_path)
    model, processor = load(model_path, {"trust_remote_code": True})
    image_processor = load_image_processor(model_path)
    return model, processor, image_processor, config


def main():
    args = parse_arguments()
    model, processor, image_processor, config = get_model_and_processors(args.model)

    prompt = codecs.decode(args.prompt, "unicode_escape")

    if "chat_template" in processor.__dict__.keys():
        prompt = processor.apply_chat_template(
            [get_message_json(config["model_type"], prompt)],
            tokenize=False,
            add_generation_prompt=True,
        )

    elif "tokenizer" in processor.__dict__.keys():
        if model.config.model_type != "paligemma":
            prompt = processor.tokenizer.apply_chat_template(
                [get_message_json(config["model_type"], prompt)],
                tokenize=False,
                add_generation_prompt=True,
            )

    else:
        raise ValueError(
            "Error: processor does not have 'chat_template' or 'tokenizer' attribute."
        )

    output = generate(
        model,
        processor,
        args.image,
        prompt,
        image_processor,
        args.temp,
        args.max_tokens,
        args.verbose,
    )
    if not args.verbose:
        print(output)


if __name__ == "__main__":
    main()
