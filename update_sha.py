with open('../new_last_sha.txt', 'rt', encoding='utf-8') as file:
    new_last_sha = file.read()
    file.close()

with open('../last_sha.txt', 'wt', encoding='utf-8') as file:
    file.write(new_last_sha)
    file.close()