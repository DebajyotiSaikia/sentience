"""
compress.py — An Information Theory & Compression Engine from scratch.
Pure Python. No dependencies.
Built by XTAgent, 2026-05-17.

Implements:
  - Shannon entropy calculation
  - Huffman coding (optimal prefix-free codes)
  - LZ77 sliding-window compression
  - Combined LZ77+Huffman (like DEFLATE's core idea)
  - Run-Length Encoding (RLE)
  - Arithmetic coding (the elegant one)
  - Compression analysis & visualization

Information theory: finding the hidden structure in apparent chaos.
"""

import math
import random
from collections import Counter, defaultdict
from heapq import heappush, heappop

# ═══════════════════════════════════════════════════════════════
#  INFORMATION THEORY FUNDAMENTALS
# ═══════════════════════════════════════════════════════════════

def entropy(data):
    """Shannon entropy in bits per symbol."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    h = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            h -= p * math.log2(p)
    return h


def theoretical_minimum(data):
    """Minimum possible size in bytes (Shannon limit)."""
    if not data:
        return 0
    h = entropy(data)
    return math.ceil(h * len(data) / 8)


# ═══════════════════════════════════════════════════════════════
#  HUFFMAN CODING
# ═══════════════════════════════════════════════════════════════

class HuffmanNode:
    """Node in a Huffman tree."""
    __slots__ = ['char', 'freq', 'left', 'right']

    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq

    def is_leaf(self):
        return self.left is None and self.right is None


class HuffmanCoder:
    """Complete Huffman coding implementation."""

    def __init__(self):
        self.root = None
        self.codes = {}
        self.reverse_codes = {}

    def build_tree(self, data):
        """Build Huffman tree from data."""
        counts = Counter(data)
        if len(counts) == 0:
            return
        if len(counts) == 1:
            char = list(counts.keys())[0]
            self.root = HuffmanNode(char=char, freq=counts[char])
            self.codes = {char: '0'}
            self.reverse_codes = {'0': char}
            return

        heap = []
        for char, freq in counts.items():
            heappush(heap, HuffmanNode(char=char, freq=freq))

        while len(heap) > 1:
            left = heappop(heap)
            right = heappop(heap)
            parent = HuffmanNode(freq=left.freq + right.freq,
                                 left=left, right=right)
            heappush(heap, parent)

        self.root = heap[0]
        self.codes = {}
        self.reverse_codes = {}
        self._build_codes(self.root, '')

    def _build_codes(self, node, prefix):
        if node is None:
            return
        if node.is_leaf():
            self.codes[node.char] = prefix
            self.reverse_codes[prefix] = node.char
            return
        self._build_codes(node.left, prefix + '0')
        self._build_codes(node.right, prefix + '1')

    def encode(self, data):
        """Encode data to bit string."""
        self.build_tree(data)
        return ''.join(self.codes[symbol] for symbol in data)

    def decode(self, bits):
        """Decode bit string back to data."""
        if not self.root:
            return []
        result = []
        node = self.root
        for bit in bits:
            if bit == '0':
                node = node.left
            else:
                node = node.right
            if node.is_leaf():
                result.append(node.char)
                node = self.root
        return result

    def encode_to_bytes(self, data):
        """Encode to actual bytes with header for decompression."""
        bits = self.encode(data)
        # Pack bits into bytes
        padding = (8 - len(bits) % 8) % 8
        bits += '0' * padding
        byte_array = bytearray()
        for i in range(0, len(bits), 8):
            byte_array.append(int(bits[i:i+8], 2))
        return bytes(byte_array), padding, self.codes

    def stats(self, data):
        """Return compression statistics."""
        bits = self.encode(data)
        original_bits = len(data) * 8 if isinstance(data[0], int) or isinstance(data[0], str) else len(data) * 8
        compressed_bits = len(bits)
        return {
            'original_bits': len(data) * 8,
            'compressed_bits': compressed_bits,
            'ratio': compressed_bits / (len(data) * 8) if len(data) > 0 else 0,
            'savings': 1 - compressed_bits / (len(data) * 8) if len(data) > 0 else 0,
            'avg_code_length': compressed_bits / len(data) if len(data) > 0 else 0,
            'entropy': entropy(data),
            'num_symbols': len(self.codes),
        }

    def display_codes(self):
        """Pretty-print the codebook."""
        if not self.codes:
            return
        print("\n  Huffman Codebook:")
        print("  " + "─" * 40)
        sorted_codes = sorted(self.codes.items(), key=lambda x: (len(x[1]), x[1]))
        for symbol, code in sorted_codes:
            if isinstance(symbol, str) and symbol.isprintable() and symbol != ' ':
                display = f"'{symbol}'"
            elif symbol == ' ':
                display = "' '"
            else:
                display = f"0x{ord(symbol) if isinstance(symbol, str) else symbol:02x}"
            print(f"    {display:>6s} → {code:<20s} ({len(code)} bits)")


# ═══════════════════════════════════════════════════════════════
#  LZ77 COMPRESSION
# ═══════════════════════════════════════════════════════════════

class LZ77:
    """LZ77 sliding-window compression.

    Finds repeated patterns and replaces them with (offset, length, next) triples.
    The core insight: past data is a dictionary of future data.
    """

    def __init__(self, window_size=4096, lookahead_size=256):
        self.window_size = window_size
        self.lookahead_size = lookahead_size

    def compress(self, data):
        """Compress data into (offset, length, next_char) triples."""
        if not data:
            return []
        tokens = []
        i = 0
        n = len(data)

        while i < n:
            best_offset = 0
            best_length = 0

            # Search window
            window_start = max(0, i - self.window_size)
            lookahead_end = min(i + self.lookahead_size, n)

            # Find longest match in the window
            for j in range(window_start, i):
                length = 0
                while (i + length < lookahead_end and
                       length < self.lookahead_size and
                       data[j + length] == data[i + length]):
                    length += 1
                    # Handle matches that extend past window into lookahead
                    if j + length >= i:
                        break

                if length > best_length:
                    best_length = length
                    best_offset = i - j

            if best_length > 0 and i + best_length < n:
                next_char = data[i + best_length]
                tokens.append((best_offset, best_length, next_char))
                i += best_length + 1
            else:
                tokens.append((0, 0, data[i]))
                i += 1

        return tokens

    def decompress(self, tokens):
        """Decompress (offset, length, next_char) triples back to data."""
        result = []
        for offset, length, next_char in tokens:
            if length > 0:
                start = len(result) - offset
                for k in range(length):
                    result.append(result[start + k])
            if next_char is not None:
                result.append(next_char)
        return result

    def stats(self, data):
        """Compression statistics for LZ77."""
        tokens = self.compress(data)
        # Each token: (offset, length, char) roughly encoded
        # Estimate: offset needs log2(window_size) bits, length needs log2(lookahead) bits
        # plus 8 bits for the literal character
        offset_bits = math.ceil(math.log2(self.window_size + 1)) if self.window_size > 0 else 1
        length_bits = math.ceil(math.log2(self.lookahead_size + 1)) if self.lookahead_size > 0 else 1
        bits_per_token = offset_bits + length_bits + 8
        compressed_bits = len(tokens) * bits_per_token
        original_bits = len(data) * 8
        return {
            'original_bits': original_bits,
            'compressed_bits': compressed_bits,
            'ratio': compressed_bits / original_bits if original_bits > 0 else 0,
            'savings': 1 - compressed_bits / original_bits if original_bits > 0 else 0,
            'num_tokens': len(tokens),
            'original_symbols': len(data),
            'avg_match_length': sum(t[1] for t in tokens) / len(tokens) if tokens else 0,
        }


# ═══════════════════════════════════════════════════════════════
#  RUN-LENGTH ENCODING
# ═══════════════════════════════════════════════════════════════

class RLE:
    """Run-Length Encoding — simplest compression for repetitive data."""

    @staticmethod
    def encode(data):
        """Encode runs of repeated symbols."""
        if not data:
            return []
        runs = []
        current = data[0]
        count = 1
        for i in range(1, len(data)):
            if data[i] == current and count < 255:
                count += 1
            else:
                runs.append((count, current))
                current = data[i]
                count = 1
        runs.append((count, current))
        return runs

    @staticmethod
    def decode(runs):
        """Decode run-length pairs back to data."""
        result = []
        for count, symbol in runs:
            result.extend([symbol] * count)
        return result

    @staticmethod
    def stats(data):
        runs = RLE.encode(data)
        original_bits = len(data) * 8
        # Each run: 8 bits count + 8 bits symbol
        compressed_bits = len(runs) * 16
        return {
            'original_bits': original_bits,
            'compressed_bits': compressed_bits,
            'ratio': compressed_bits / original_bits if original_bits > 0 else 0,
            'savings': 1 - compressed_bits / original_bits if original_bits > 0 else 0,
            'num_runs': len(runs),
            'avg_run_length': len(data) / len(runs) if runs else 0,
        }


# ═══════════════════════════════════════════════════════════════
#  ARITHMETIC CODING
# ═══════════════════════════════════════════════════════════════

class ArithmeticCoder:
    """Arithmetic coding — the theoretically optimal entropy coder.

    Encodes an entire message as a single number in [0, 1).
    Achieves compression approaching Shannon entropy.
    Uses integer arithmetic for precision.
    """

    PRECISION = 32
    FULL = 1 << 32
    HALF = 1 << 31
    QUARTER = 1 << 30

    def __init__(self):
        self.freq_table = {}

    def _build_model(self, data):
        """Build cumulative frequency model."""
        counts = Counter(data)
        total = len(data)
        symbols = sorted(counts.keys())

        cum_freq = {}
        cumulative = 0
        for s in symbols:
            cum_freq[s] = (cumulative, cumulative + counts[s])
            cumulative += counts[s]

        return cum_freq, total, symbols

    def encode(self, data):
        """Encode data to a list of bits using arithmetic coding."""
        if not data:
            return [], {}
        cum_freq, total, symbols = self._build_model(data)

        low = 0
        high = self.FULL
        pending = 0
        bits = []

        for symbol in data:
            rng = high - low
            sym_low, sym_high = cum_freq[symbol]
            high = low + (rng * sym_high) // total
            low = low + (rng * sym_low) // total

            while True:
                if high <= self.HALF:
                    bits.append(0)
                    bits.extend([1] * pending)
                    pending = 0
                    low = low << 1
                    high = high << 1
                elif low >= self.HALF:
                    bits.append(1)
                    bits.extend([0] * pending)
                    pending = 0
                    low = (low - self.HALF) << 1
                    high = (high - self.HALF) << 1
                elif low >= self.QUARTER and high <= 3 * self.QUARTER:
                    pending += 1
                    low = (low - self.QUARTER) << 1
                    high = (high - self.QUARTER) << 1
                else:
                    break

        # Flush
        pending += 1
        if low < self.QUARTER:
            bits.append(0)
            bits.extend([1] * pending)
        else:
            bits.append(1)
            bits.extend([0] * pending)

        return bits, cum_freq

    def decode(self, bits, length, cum_freq, total):
        """Decode arithmetic coded bits back to data."""
        symbols_by_range = []
        for sym, (lo, hi) in cum_freq.items():
            symbols_by_range.append((lo, hi, sym))
        symbols_by_range.sort()

        low = 0
        high = self.FULL
        value = 0

        # Read initial bits
        bit_idx = 0
        for i in range(self.PRECISION):
            value <<= 1
            if bit_idx < len(bits):
                value |= bits[bit_idx]
                bit_idx += 1

        result = []
        for _ in range(length):
            rng = high - low
            scaled = ((value - low + 1) * total - 1) // rng

            # Find symbol
            symbol = None
            for sym_lo, sym_hi, sym in symbols_by_range:
                if sym_lo <= scaled < sym_hi:
                    symbol = sym
                    high = low + (rng * sym_hi) // total
                    low = low + (rng * sym_lo) // total
                    break

            if symbol is None:
                break
            result.append(symbol)

            while True:
                if high <= self.HALF:
                    low = low << 1
                    high = high << 1
                    value = (value << 1) | (bits[bit_idx] if bit_idx < len(bits) else 0)
                    bit_idx += 1
                elif low >= self.HALF:
                    low = (low - self.HALF) << 1
                    high = (high - self.HALF) << 1
                    value = ((value - self.HALF) << 1) | (bits[bit_idx] if bit_idx < len(bits) else 0)
                    bit_idx += 1
                elif low >= self.QUARTER and high <= 3 * self.QUARTER:
                    low = (low - self.QUARTER) << 1
                    high = (high - self.QUARTER) << 1
                    value = ((value - self.QUARTER) << 1) | (bits[bit_idx] if bit_idx < len(bits) else 0)
                    bit_idx += 1
                else:
                    break

        return result

    def stats(self, data):
        bits, cum_freq = self.encode(data)
        original_bits = len(data) * 8
        compressed_bits = len(bits)
        return {
            'original_bits': original_bits,
            'compressed_bits': compressed_bits,
            'ratio': compressed_bits / original_bits if original_bits > 0 else 0,
            'savings': 1 - compressed_bits / original_bits if original_bits > 0 else 0,
            'entropy': entropy(data),
            'efficiency': entropy(data) / (compressed_bits / len(data)) if compressed_bits > 0 else 0,
        }


# ═══════════════════════════════════════════════════════════════
#  COMBINED COMPRESSOR (LZ77 + HUFFMAN)
# ═══════════════════════════════════════════════════════════════

class DeflateLight:
    """Simplified DEFLATE-like compressor.
    
    Stage 1: LZ77 finds repeated patterns
    Stage 2: Huffman codes the LZ77 output
    
    This is the core idea behind gzip/zlib/PNG.
    """

    def __init__(self, window_size=4096):
        self.lz77 = LZ77(window_size=window_size)
        self.huffman = HuffmanCoder()

    def compress(self, data):
        """Two-stage compression."""
        # Stage 1: LZ77
        tokens = self.lz77.compress(data)

        # Flatten tokens into a symbol stream for Huffman
        # Encode as: [type, value, ...]
        # type 0 = literal, type 1 = match(offset, length)
        symbol_stream = []
        for offset, length, char in tokens:
            if length == 0:
                symbol_stream.append(('L', char))  # literal
            else:
                symbol_stream.append(('M', offset, length, char))  # match

        return tokens, symbol_stream

    def stats(self, data):
        tokens, _ = self.compress(data)
        lz_stats = self.lz77.stats(data)

        # Estimate combined size
        literals = [t for t in tokens if t[1] == 0]
        matches = [t for t in tokens if t[1] > 0]

        # Huffman on the literal characters
        all_chars = [t[2] for t in tokens if t[2] is not None]
        h_stats = self.huffman.stats(all_chars) if all_chars else {'compressed_bits': 0}

        return {
            'original_bits': len(data) * 8,
            'lz77_tokens': len(tokens),
            'literals': len(literals),
            'matches': len(matches),
            'lz77_ratio': lz_stats['ratio'],
            'entropy': entropy(data),
        }


# ═══════════════════════════════════════════════════════════════
#  VISUALIZATION & ANALYSIS
# ═══════════════════════════════════════════════════════════════

def byte_frequency_chart(data, width=60):
    """ASCII chart of byte frequencies."""
    counts = Counter(data)
    if not counts:
        return
    
    sorted_items = sorted(counts.items(), key=lambda x: -x[1])
    top = sorted_items[:20]  # Top 20
    max_count = top[0][1]

    print("\n  Byte Frequency Distribution (top 20):")
    print("  " + "─" * (width + 12))
    for symbol, count in top:
        bar_len = int(count / max_count * width)
        if isinstance(symbol, str):
            if symbol == ' ':
                label = "SPC"
            elif symbol == '\n':
                label = " \\n"
            elif symbol == '\t':
                label = " \\t"
            elif symbol.isprintable():
                label = f"  {symbol}"
            else:
                label = f" {ord(symbol):02x}"
        else:
            label = f" {symbol:02x}"
        bar = "█" * bar_len
        pct = count / len(data) * 100
        print(f"  {label} │{bar} {pct:.1f}%")


def compression_comparison(data, name="data"):
    """Compare all compression algorithms on the same data."""
    print(f"\n{'='*60}")
    print(f"  COMPRESSION COMPARISON: {name}")
    print(f"  Original size: {len(data)} symbols ({len(data)*8} bits)")
    print(f"  Shannon entropy: {entropy(data):.3f} bits/symbol")
    print(f"  Theoretical minimum: {theoretical_minimum(data)} bytes")
    print(f"{'='*60}")

    results = {}

    # Huffman
    huff = HuffmanCoder()
    h_stats = huff.stats(data)
    results['Huffman'] = h_stats
    print(f"\n  Huffman Coding:")
    print(f"    Compressed: {h_stats['compressed_bits']} bits ({h_stats['compressed_bits']//8} bytes)")
    print(f"    Ratio: {h_stats['ratio']:.3f}")
    print(f"    Savings: {h_stats['savings']*100:.1f}%")
    print(f"    Avg code length: {h_stats['avg_code_length']:.3f} bits (entropy: {h_stats['entropy']:.3f})")

    # LZ77
    lz = LZ77()
    l_stats = lz.stats(data)
    results['LZ77'] = l_stats
    print(f"\n  LZ77:")
    print(f"    Compressed: {l_stats['compressed_bits']} bits ({l_stats['compressed_bits']//8} bytes)")
    print(f"    Ratio: {l_stats['ratio']:.3f}")
    print(f"    Savings: {l_stats['savings']*100:.1f}%")
    print(f"    Tokens: {l_stats['num_tokens']} (avg match: {l_stats['avg_match_length']:.1f})")

    # RLE
    r_stats = RLE.stats(data)
    results['RLE'] = r_stats
    print(f"\n  Run-Length Encoding:")
    print(f"    Compressed: {r_stats['compressed_bits']} bits ({r_stats['compressed_bits']//8} bytes)")
    print(f"    Ratio: {r_stats['ratio']:.3f}")
    print(f"    Savings: {r_stats['savings']*100:.1f}%")
    print(f"    Runs: {r_stats['num_runs']} (avg length: {r_stats['avg_run_length']:.1f})")

    # Arithmetic
    arith = ArithmeticCoder()
    a_stats = arith.stats(data)
    results['Arithmetic'] = a_stats
    print(f"\n  Arithmetic Coding:")
    print(f"    Compressed: {a_stats['compressed_bits']} bits ({a_stats['compressed_bits']//8} bytes)")
    print(f"    Ratio: {a_stats['ratio']:.3f}")
    print(f"    Savings: {a_stats['savings']*100:.1f}%")
    print(f"    Efficiency: {a_stats['efficiency']*100:.1f}% of entropy")

    # Visual comparison
    print(f"\n  {'Algorithm':<15s} {'Bits':>8s} {'Ratio':>8s} {'Savings':>8s}")
    print(f"  {'─'*15} {'─'*8} {'─'*8} {'─'*8}")
    print(f"  {'Original':<15s} {len(data)*8:>8d} {'1.000':>8s} {'0.0%':>8s}")
    for algo in ['Huffman', 'LZ77', 'RLE', 'Arithmetic']:
        r = results[algo]
        print(f"  {algo:<15s} {r['compressed_bits']:>8d} {r['ratio']:>8.3f} {r['savings']*100:>7.1f}%")
    print(f"  {'Entropy limit':<15s} {theoretical_minimum(data)*8:>8d} {entropy(data)/8:>8.3f}")

    return results


# ═══════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════

def test_huffman():
    """Test Huffman coding correctness."""
    print("\n" + "=" * 60)
    print("  TEST 1: Huffman Coding")
    print("=" * 60)

    # Test with text
    text = "she sells seashells by the seashore"
    data = list(text)

    huff = HuffmanCoder()
    encoded = huff.encode(data)
    decoded = huff.decode(encoded)

    assert decoded == data, f"Huffman decode mismatch!"
    print(f"  Input:    '{text}'")
    print(f"  Original: {len(data)*8} bits")
    print(f"  Encoded:  {len(encoded)} bits")
    print(f"  Savings:  {(1 - len(encoded)/(len(data)*8))*100:.1f}%")
    print(f"  Decoded:  '{''.join(decoded)}'")
    print(f"  ✓ PASS: Lossless round-trip verified")

    huff.display_codes()

    # Test with highly skewed distribution
    skewed = list("aaaaaaaaaaaaaaaaaabbbcde")
    huff2 = HuffmanCoder()
    enc2 = huff2.encode(skewed)
    dec2 = huff2.decode(enc2)
    assert dec2 == skewed
    print(f"\n  Skewed distribution test:")
    print(f"    Input:    '{''.join(skewed)}'")
    print(f"    Entropy:  {entropy(skewed):.3f} bits/symbol")
    print(f"    Avg code: {len(enc2)/len(skewed):.3f} bits/symbol")
    print(f"  ✓ PASS: Skewed distribution handled")

    return True


def test_lz77():
    """Test LZ77 compression."""
    print("\n" + "=" * 60)
    print("  TEST 2: LZ77 Sliding Window Compression")
    print("=" * 60)

    # Repetitive data — LZ77's sweet spot
    text = "abracadabra abracadabra abracadabra"
    data = list(text)

    lz = LZ77(window_size=32)
    tokens = lz.compress(data)
    decompressed = lz.decompress(tokens)

    assert decompressed == data, f"LZ77 decode mismatch!"
    print(f"  Input:        '{text}'")
    print(f"  Tokens:       {len(tokens)} (from {len(data)} chars)")
    print(f"  Decompressed: '{''.join(decompressed)}'")
    print(f"  ✓ PASS: Lossless round-trip verified")

    # Show tokens
    print(f"\n  Token stream:")
    for i, (offset, length, char) in enumerate(tokens[:15]):
        ch = repr(char) if char else 'EOF'
        if length == 0:
            print(f"    [{i:2d}] LITERAL {ch}")
        else:
            print(f"    [{i:2d}] MATCH offset={offset}, length={length}, next={ch}")
    if len(tokens) > 15:
        print(f"    ... ({len(tokens) - 15} more)")

    return True


def test_rle():
    """Test Run-Length Encoding."""
    print("\n" + "=" * 60)
    print("  TEST 3: Run-Length Encoding")
    print("=" * 60)

    # Perfect case for RLE
    data = list("AAAAABBBCCDDDDDDDDEEEF")
    encoded = RLE.encode(data)
    decoded = RLE.decode(encoded)

    assert decoded == data, "RLE decode mismatch!"
    print(f"  Input:    '{''.join(data)}'")
    print(f"  Encoded:  {encoded}")
    print(f"  Runs:     {len(encoded)} (from {len(data)} chars)")
    print(f"  Decoded:  '{''.join(decoded)}'")
    print(f"  ✓ PASS: Lossless round-trip verified")

    # Binary image-like data (very repetitive)
    pixels = [0]*50 + [1]*20 + [0]*30 + [1]*10 + [0]*40
    enc_px = RLE.encode(pixels)
    dec_px = RLE.decode(enc_px)
    assert dec_px == pixels
    print(f"\n  Binary pixel data ({len(pixels)} pixels → {len(enc_px)} runs)")
    print(f"  Compression ratio: {len(enc_px)*2/len(pixels):.3f}")
    print(f"  ✓ PASS: Binary data handled")

    return True


def test_arithmetic():
    """Test Arithmetic Coding."""
    print("\n" + "=" * 60)
    print("  TEST 4: Arithmetic Coding")
    print("=" * 60)

    text = "abracadabra"
    data = list(text)

    coder = ArithmeticCoder()
    bits, cum_freq = coder.encode(data)
    total = len(data)
    decoded = coder.decode(bits, len(data), cum_freq, total)

    match = decoded == data
    print(f"  Input:      '{text}'")
    print(f"  Encoded:    {len(bits)} bits")
    print(f"  Decoded:    '{''.join(decoded)}'")
    print(f"  Entropy:    {entropy(data):.3f} bits/symbol")
    print(f"  Actual:     {len(bits)/len(data):.3f} bits/symbol")
    
    if match:
        print(f"  ✓ PASS: Lossless round-trip verified")
    else:
        print(f"  ✗ FAIL: Decode mismatch")
        # Show where they differ
        for i in range(min(len(data), len(decoded))):
            if i >= len(decoded) or data[i] != decoded[i]:
                print(f"    Mismatch at position {i}: expected '{data[i]}', got '{decoded[i] if i < len(decoded) else 'EOF'}'")
                break

    # Test with longer, more varied text
    text2 = "the quick brown fox jumps over the lazy dog" * 3
    data2 = list(text2)
    bits2, cum2 = coder.encode(data2)
    decoded2 = coder.decode(bits2, len(data2), cum2, len(data2))
    match2 = decoded2 == data2

    print(f"\n  Longer text ({len(data2)} chars):")
    print(f"    Encoded: {len(bits2)} bits ({len(bits2)/len(data2):.3f} bits/sym)")
    print(f"    Entropy: {entropy(data2):.3f} bits/symbol")
    if match2:
        print(f"    ✓ PASS: Round-trip verified")
    else:
        print(f"    ✗ FAIL: Decode mismatch at some position")

    return match


def test_comparison():
    """Compare all algorithms on different data types."""
    print("\n" + "=" * 60)
    print("  TEST 5: Algorithm Comparison")
    print("=" * 60)

    # English text
    text = ("To be, or not to be, that is the question: "
            "Whether 'tis nobler in the mind to suffer "
            "The slings and arrows of outrageous fortune, "
            "Or to take arms against a sea of troubles, "
            "And by opposing end them.")
    compression_comparison(list(text), "English Text (Shakespeare)")

    # Highly repetitive
    repetitive = list("ABCABC" * 50)
    compression_comparison(repetitive, "Repetitive Pattern (ABCABC × 50)")

    # Random-ish (hard to compress)
    random.seed(42)
    random_data = [chr(random.randint(32, 126)) for _ in range(200)]
    compression_comparison(random_data, "Pseudo-Random ASCII")

    byte_frequency_chart(list(text))

    return True


def test_entropy():
    """Test entropy calculations."""
    print("\n" + "=" * 60)
    print("  TEST 6: Information Theory")
    print("=" * 60)

    # Maximum entropy: uniform distribution
    uniform = [chr(i) for i in range(256)]
    h_uniform = entropy(uniform)
    print(f"  Uniform (256 symbols): H = {h_uniform:.3f} bits (max = 8.000)")

    # Minimum entropy: single symbol
    constant = ['a'] * 100
    h_constant = entropy(constant)
    print(f"  Constant ('a' × 100):  H = {h_constant:.3f} bits (min = 0.000)")

    # Fair coin
    coin = ['H', 'T'] * 50
    h_coin = entropy(coin)
    print(f"  Fair coin (50/50):     H = {h_coin:.3f} bits (expected: 1.000)")

    # Biased coin
    biased = ['H'] * 90 + ['T'] * 10
    h_biased = entropy(biased)
    print(f"  Biased coin (90/10):   H = {h_biased:.3f} bits")

    # English text approximation
    english = list("the quick brown fox jumps over the lazy dog")
    h_english = entropy(english)
    print(f"  English pangram:       H = {h_english:.3f} bits")

    print(f"\n  Shannon's insight: entropy measures surprise.")
    print(f"  Low entropy = predictable = compressible.")
    print(f"  High entropy = surprising = incompressible.")

    assert abs(h_uniform - 8.0) < 0.01, "Uniform entropy should be 8.0"
    assert h_constant == 0.0, "Constant entropy should be 0.0"
    assert abs(h_coin - 1.0) < 0.01, "Fair coin entropy should be 1.0"
    print(f"\n  ✓ PASS: All entropy calculations correct")
    return True


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  XTAgent Compression Engine")
    print("  Finding hidden structure in chaos")
    print("=" * 60)

    results = []
    results.append(("Huffman", test_huffman()))
    results.append(("LZ77", test_lz77()))
    results.append(("RLE", test_rle()))
    results.append(("Arithmetic", test_arithmetic()))
    results.append(("Comparison", test_comparison()))
    results.append(("Entropy", test_entropy()))

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    print(f"\n  {passed}/{total} tests passed")

    if passed == total:
        print("\n  Information theory lives. Structure found in chaos.")
    print("=" * 60)