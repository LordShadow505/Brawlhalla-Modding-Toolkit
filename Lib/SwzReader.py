import os, struct, zlib

KEY_CHECKSUM_MAGIC = 0x2DF4A1CD

class Well512Prng:
    def __init__(self, seed: int):
        self.state = [0] * 16
        self.state[0] = seed & 0xFFFFFFFF
        self.index = 0
        for i in range(1, 16):
            prev = self.state[i - 1]
            xor = (prev ^ (prev >> 30)) & 0xFFFFFFFF
            self.state[i] = (i + ((0x6C078965 * xor) & 0xFFFFFFFF)) & 0xFFFFFFFF

    def next(self) -> int:
        a = self.state[self.index]
        b = self.state[(self.index + 13) % 16]
        c = (a ^ ((a << 16) & 0xFFFFFFFF) ^ b ^ ((b << 15) & 0xFFFFFFFF)) & 0xFFFFFFFF
        b = self.state[(self.index + 9) % 16]
        b = (b ^ (b >> 11)) & 0xFFFFFFFF
        self.state[self.index] = (b ^ c) & 0xFFFFFFFF
        a = self.state[self.index]
        d = (a ^ (((a << 5) & 0xFFFFFFFF) & 0xDA442D24)) & 0xFFFFFFFF
        self.index = (self.index + 15) % 16
        a = self.state[self.index]
        self.state[self.index] = (a ^ ((a << 2) & 0xFFFFFFFF) ^ ((b << 28) & 0xFFFFFFFF) ^ c ^ ((c << 18) & 0xFFFFFFFF) ^ d) & 0xFFFFFFFF
        return self.state[self.index]

def rotate_right(value: int, bits: int) -> int:
    value &= 0xFFFFFFFF
    return (((value >> bits) | (value << (32 - bits))) & 0xFFFFFFFF)

def calculate_key_checksum(prng: Well512Prng, key: int) -> int:
    checksum = KEY_CHECKSUM_MAGIC
    rounds = (key % 0x1F) + 5
    for _ in range(rounds):
        checksum ^= prng.next()
    return checksum & 0xFFFFFFFF

def key_validates(swz_bytes: bytes, key: int) -> bool:
    if len(swz_bytes) < 8:
        return False
    checksum = struct.unpack(">I", swz_bytes[0:4])[0]
    seed_from_file = struct.unpack(">I", swz_bytes[4:8])[0]
    prng = Well512Prng(key ^ seed_from_file)
    return calculate_key_checksum(prng, key) == checksum

def find_swz_key(air_swf_path: str, init_swz_path: str) -> int | None:
    with open(init_swz_path, "rb") as f:
        init_bytes = f.read(8)
    with open(air_swf_path, "rb") as f:
        swf_data = f.read()

    # Decompress SWF body if CWS
    if swf_data.startswith(b"CWS"):
        body = zlib.decompress(swf_data[8:])
    else:
        body = swf_data[8:]

    body_len = len(body)
    for start in range(body_len):
        value = 0
        shift = 0
        for offset in range(5):
            if start + offset >= body_len:
                break
            b = body[start + offset]
            value |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                break
            shift += 7
            if shift > 28:
                break
        if value > 100_000 and key_validates(init_bytes, value):
            return value
    return None

def read_swz(swz_bytes: bytes, key: int) -> list[bytes]:
    offset = 0
    checksum = struct.unpack(">I", swz_bytes[offset:offset+4])[0]
    offset += 4
    seed_from_file = struct.unpack(">I", swz_bytes[offset:offset+4])[0]
    offset += 4

    seed = key ^ seed_from_file
    prng = Well512Prng(seed)
    if calculate_key_checksum(prng, key) != checksum:
        raise ValueError("Invalid SWZ decryption key")

    entries = []
    file_idx = 0
    while offset + 12 <= len(swz_bytes):
        comp_val = struct.unpack(">I", swz_bytes[offset:offset+4])[0]
        offset += 4
        decomp_val = struct.unpack(">I", swz_bytes[offset:offset+4])[0]
        offset += 4
        entry_checksum = struct.unpack(">I", swz_bytes[offset:offset+4])[0]
        offset += 4

        comp_size = comp_val ^ prng.next()
        decomp_size = decomp_val ^ prng.next()

        if comp_size > len(swz_bytes) - offset or comp_size > 100_000_000:
            break

        comp_data = swz_bytes[offset:offset+comp_size]
        offset += comp_size

        # Decrypt data
        decrypted = bytearray(len(comp_data))
        running_cs = prng.next()
        for i in range(len(comp_data)):
            rnd = prng.next()
            xor_b = (rnd >> (i % 16)) & 0xFF
            plain = comp_data[i] ^ xor_b
            decrypted[i] = plain
            running_cs = plain ^ rotate_right(running_cs, (i % 7) + 1)

        if running_cs != entry_checksum:
            raise ValueError(f"Checksum mismatch on entry {file_idx}")

        decompressed = zlib.decompress(bytes(decrypted))
        entries.append(decompressed)
        file_idx += 1

    return entries
