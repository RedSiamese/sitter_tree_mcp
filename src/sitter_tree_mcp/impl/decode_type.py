def guess_encoder(data: bytes) -> str:
    encodings = ['utf-8', 'gb2312', 'gbk', 'big5', 'latin1', 'ascii']  # 常见编码列表
    for encoding in encodings:
        try:
            _ = data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'
