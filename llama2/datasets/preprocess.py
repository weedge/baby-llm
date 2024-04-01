import os
import argparse

import sentencepiece as spm
from sentencepiece import sentencepiece_model_pb2 as sp_pb2_model
from transformers import LlamaTokenizer

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"


def merge_tokenizer(data_dir, merge_tokenizer_model, src_tokenizer_model="meta-llama/Llama-2-7b-hf"):
    """
    merge tokenizer sp pb2 format model, save to huggingface format model
    """
    llama_tokenizer = LlamaTokenizer.from_pretrained(src_tokenizer_model)
    llama_spm = sp_pb2_model.ModelProto()
    llama_spm.ParseFromString(
        llama_tokenizer.sp_model.serialized_model_proto())

    merge_sp_model = spm.SentencePieceProcessor()
    merge_sp_model.Load(merge_tokenizer_model)
    merge_spm = sp_pb2_model.ModelProto()
    merge_spm.ParseFromString(merge_sp_model.serialized_model_proto())

    llama_spm_tokens_set = set(p.piece for p in llama_spm.pieces)
    print(f"before src_tokens:{len(llama_spm_tokens_set)}")
    for p in merge_spm.pieces:
        piece = p.piece
        if piece not in llama_spm_tokens_set:
            new_p = sp_pb2_model.ModelProto().SentencePiece()
            new_p.piece = piece
            new_p.score = 0
            llama_spm.pieces.append(new_p)
    print(f"New model pieces: {len(llama_spm.pieces)}")

    # 保存合并后的模型(pb序列化)
    output_sp_dir = os.path.join(data_dir, 'merged_tokenizer_sp')
    output_hf_dir = os.path.join(data_dir, 'merged_tokenizer_hf')
    os.makedirs(output_sp_dir, exist_ok=True)
    tokenizer_vocab_model_file = output_sp_dir+'/new_llama_tokenizer.model'
    with open(tokenizer_vocab_model_file, 'wb') as f:
        f.write(llama_spm.SerializeToString())
        print(
            f"{merge_sp_model} tokenizer has been saved to {tokenizer_vocab_model_file}")
    tokenizer = LlamaTokenizer(vocab_file=tokenizer_vocab_model_file)

    tokenizer.save_pretrained(output_hf_dir)
    print(f"{merge_sp_model} tokenizer has been saved to hf tokenizer {output_hf_dir}")


def print_tokenizer(tokenizer_model):
    mp = sp_pb2_model.ModelProto()
    mp.ParseFromString(open(tokenizer_model, "rb").read())
    print(mp.trainer_spec)
    print(mp.normalizer_spec)


if __name__ == "__main__":
    """
    These stages are designed to be run in order.

    To tokenize data with a custom tokenizer we train ourselves with sentencepiece, e.g.:
    python preprocess.py merge_tokenizer --data_dir=./datas --src_tokenizer_model=${src} --merge_tokenizer_model=${merge}
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", type=str, choices=[
                        "train_vocab", "merge_tokenizer", "pretokenize", "print_tokenizer"])
    parser.add_argument("--data_dir", type=str,
                        default="./datas", help="process data dir")
    parser.add_argument("--src_tokenizer_model", type=str,
                        default="", help="src tokenizer model file")
    parser.add_argument("--merge_tokenizer_model", type=str,
                        default="", help="merge tokenizer model file")
    args = parser.parse_args()

    # depending on the stage call the appropriate function
    if args.stage == "merge_tokenizer":
        merge_tokenizer(data_dir=args.data_dir,
                        merge_tokenizer_model=args.merge_tokenizer_model,
                        src_tokenizer_model=args.src_tokenizer_model)
    elif args.stage == "print_tokenizer":
        print_tokenizer(tokenizer_model=args.tokenizer_model)
    else:
        raise ValueError(f"Unknown stage {args.stage}")