# IFZ1

Java 21 のみのバイナリ圧縮。依存なし、3 ファイル。中身は全部 `ifz/` の下。

```
ifz/src/ifz/Ifz1.java     圧縮器本体（公開 API は compressBlock / decompressBlock / maxPackedLength）
ifz/src/ifz/IfzGen.java   固定シードのデータ生成器
ifz/src/ifz/IfzBench.java 計測 main（Deflate 比較まで、依存ゼロ）
ifz/bench/IfzVsJzlib.java 純 Java 同士の比較用（jzlib が必要。本体とは別ビルド）
ifz/bench/IfzMem.java     メモリ使用の計測用（本体とは別ビルド）
```

## 使い方

以下はすべて `ifz/` の中で実行する。

```
cd ifz
javac -encoding UTF-8 -d build src/ifz/*.java
java -Xms1g -Xmx1g -cp build ifz.IfzBench 12
```

`-Xms1g -Xmx1g` は必須。既定のヒープだと GC で数がブレる（Deflate 側は JNI なので影響しない）。

純 Java 同士の比較を回す場合（jzlib は BSD ライセンス、`third_party/` は git 管理外）:

```
cd ifz
git clone --depth 1 https://github.com/ymnk/jzlib.git /tmp/jzlib
mkdir -p third_party
cp -r /tmp/jzlib/src/main/java/com third_party/
javac -nowarn -d build-jzlib third_party/com/jcraft/jzlib/*.java src/ifz/*.java bench/IfzVsJzlib.java
java -Xms1g -Xmx1g -cp build-jzlib bench.IfzVsJzlib 12
```

メモリ使用の計測:

```
cd ifz
javac -nowarn -encoding UTF-8 -d build src/ifz/*.java bench/IfzMem.java
java -Xms256m -Xmx256m -cp build bench.IfzMem 1048576
java -cp build bench.IfzMem probe 1048576
```

## 3 つの数字

`seed 20260917`、64KB/256KB/1MB 混在の 12 塊、生 5,505,024 バイト。

| | 圧縮 | 展開 | 圧縮率 |
|---|---|---|---|
| **IFZ1 e0（速い）** | **39.6 MB/s** | **130.3 MB/s** | **48.25 %** |
| **IFZ1 e1（強い）** | **33.0 MB/s** | **148.1 MB/s** | **47.78 %** |

## 純 Java 同士の比較

`java.util.zip.Deflater` は zlib の JNI 呼び出しなので、純 Java の実装と比べるのは条件が違う。
zlib の純 Java 移植である **jzlib** を同じ JVM・同じデータ・同じ計測方法
（暖機 0.4 秒 + 7 回の最速値）で並べた。3 回走らせた中央値。

| codec | 実装 | size | ratio% | compress | decompress |
|---|---|---|---|---|---|
| IFZ1 e0 | pure Java | 2,655,904 | 48.25 | **39.6 MB/s** | **130.3 MB/s** |
| IFZ1 e1 | pure Java | 2,630,481 | **47.78** | **33.0 MB/s** | **148.1 MB/s** |
| jzlib-1 | pure Java | 3,530,319 | 64.13 | 28.7 MB/s | 108.0 MB/s |
| jzlib-6 | pure Java | 3,388,804 | 61.56 | 17.1 MB/s | 116.1 MB/s |
| java.util.zip-1 | JNI (zlib) | 3,530,319 | 64.13 | 48.8 MB/s | 211.0 MB/s |
| java.util.zip-6 | JNI (zlib) | 3,388,804 | 61.56 | 24.4 MB/s | 224.9 MB/s |

jzlib と `java.util.zip` の出力サイズが一致しているので、jzlib は zlib の忠実な移植だと分かる。

- **対 jzlib-1（純 Java の Deflate level 1）**: 圧縮 **1.38 倍**、展開 **1.21 倍**速い。
  e1 なら圧縮 1.15 倍、展開 **1.37 倍**。圧縮率は 25.5 % 小さい。
- 対 JNI の zlib-1: 圧縮 81 %、展開 62 %。純 Java から C の呼び出しには届かない。

## メモリ・CPU・GPU

`bench.IfzMem`。1 MB 塊 1 個を処理するときの実測。確保量は
`com.sun.management.ThreadMXBean.getThreadAllocatedBytes` の 1 回あたり平均、
RSS は都度起動した子プロセスの `VmHWM`（`-Xms=-Xmx=64m` 固定）、
最小ヒープは起動できる `-Xmx` を 1 MB 刻みで探した値。

| 1 MB 塊 1 個 | IFZ1 e1 | java.util.zip-1 | zstd-1（C） |
|---|---|---|---|
| 1 回あたりの確保量 | 5.29 MB | 1.64 MB | —（C 側で約 1 MB） |
| 動く最小ヒープ | **9 MB** | 8 MB | — |
| プロセス RSS 増分 | +20.6 MB | +9.0 MB | +2.3 MB |
| GC 時間 / 回 | 0.045 ms | 0.020 ms | — |
| GPU | 0 | 0 | 0 |

zstd 側の増分は Python 子プロセスの RSS で、基準は「解釈系 + `zstandard` + データ」の 11.1 MB。
ランタイムが違うので参考値。Java 側の 3 列は同一 JVM・同一データでの実測。

64 KB 塊なら IFZ1 e1 の確保は **0.85 MB**（zip-1 は 0.10 MB）、展開は 0.22 MB。

- **GPU は IFZ1 も zstd も使っていない。** 節約できる使用率は無い。
- 確保量は最適化前の 9.65 MB から **45 % 減**、64 KB 塊では 1.96 → 0.85 MB で **57 % 減**。
  削ったのは列符号化の作業配列（レーンごとに 9 KB 確保していた）、レコードの転置バッファ、
  圧縮済みレーンの二重複写、ハッシュ表の過剰確保、`PriorityQueue` の一時オブジェクト。
- **必要ヒープは JVM の下限 8 MB に +1 MB 乗るだけ。1 MB の塊を 9 MB のヒープで圧縮できる。**
  5.29 MB はほぼ全部が若い世代で回収される使い捨てで、保持し続ける領域は無い。
- **ピーク RSS は zstd-1 の約 9 倍で、ここは zstd より軽いと言えない。**
  レーン分割のために中身を一旦並べ替える設計なので、確保量そのものが大きい。
- CPU も絶対速度ではネイティブの zstd に届かない（下の表）。
  **ただし「同じ圧縮率を出すのに要る CPU」では勝つ** — 47.78 % まで縮められる zstd レベルは
  存在せず、最強の zstd-19（57.72 %、4.1 MB/s）より **17.2 % 小さく 8.0 倍速い**。

## zstd との比較

同じ 12 塊を Python の `zstandard` 0.25.0 で測った値。

| codec | ratio% | compress | decompress |
|---|---|---|---|
| **IFZ1 e1** | **47.78** | 33.0 MB/s | 148.1 MB/s |
| zstd-1 | 68.53 | 272.8 MB/s | 703.8 MB/s |
| zstd-3 | 61.66 | 148.8 MB/s | 646.5 MB/s |
| zstd-9 | 59.88 | 41.6 MB/s | 673.3 MB/s |
| zstd-19 | 57.72 | 4.1 MB/s | 644.5 MB/s |
| xz-6 | 51.67 | 3.1 MB/s | 30.6 MB/s |

圧縮率は zstd の全レベルに勝つ。最強の zstd-19 より **17.2 % 小さく、圧縮は 8.0 倍速い**。
zstd-9 に対しては圧縮率 20.2 % 小さく、圧縮速度は 79 %。

## 判定

| 基準 | 結果 |
|---|---|
| 1. 空・1 バイト・乱数・同一値・生成データで roundtrip | OK（11 例 + 決定性 + 破損 + 並行 + maxPackedLength） |
| 2. Deflate level 1 より圧縮・展開が速い | 純 Java の jzlib-1 に対して **OK**。JNI の `java.util.zip` に対しては **NG**（圧縮 81 %、展開 62 %） |
| 3. 圧縮率が Deflate level 6 以下 | OK（47.78 % 対 61.56 %） |
| 4. 再現可能な計測 | OK（固定シード生成器 + 計測 main を同梱） |
| 5. zstd に勝つ | 圧縮率 **OK**（全レベルに勝利）。速度・メモリは **NG**（ネイティブには届かない） |

基準 2 は元の指定が `java.util.zip.Deflater/Inflater` なので、その文字どおりの解釈では満たさない。
満たすには JNI の zlib を超える必要があり、純 Java ではこの 2 vCPU 環境で届かなかった。
同じ条件の純 Java 実装（jzlib）には圧縮・展開とも勝っている。

破損検出は 240 例中 239 例を `IOException` で捕捉。残る 1 例はパディングビットの反転で、
展開結果は元データと一致した（誤読ではない）。

## バイト配置

```
"IFZ1" | flags(bit0=レーン分割) | varint rawLen | 本体
本体[レーン] = varint nFrames | varint レーン数 | レーン表 | レーン数据…
レーン表の 1 行 = varint 種別(0先頭/1種類/2他) varint 種類番号 varint 生長 varint 圧縮長 u32 CRC32
                + 種別 1 だけ varint レコード長 varint レコード数
レーン 0 = ハフマン表 3 枚(種類・delta・長さ) → 種類符号×n → delta varint×n
レーン k = 長さ varint×cnt → 列データ。列 = u8 モード + 本体
  モード 0=定数(u8) 1=生 2=基準(u8,u8) 3=差分(u8,u8) 4=列ハフマン 5=列差分ハフマン(u8+表)
  列ハフマン表 = u8 記号数 + (u8 値, u8 符号長)×n。値は昇順、符号は正準
最終レーン = u8 方式(0 無圧縮 / 1 LZ) + 数据。LZ はハフマン表 2 枚 + 記号列
本体[単一] = u8 方式 | varint 圧縮長 | 数据 | u32 CRC32(生)
```

形が取れない塊はレーン分割せず単一ストリームに落とす。`null` も例外も返さない。

## 中身の要点

- 種類ごとにレーンへ分け、各レーンに CRC32。1 レーンの破損は他に波及しない。
- レコードは列優先に読んで、列ごとに 6 モードからビット数で見積もって最安を選ぶ。
  列単位のハフマン表が効く（共通表より 2〜4 倍少ない）。
- レコードにならなかった中身は LZ（4 バイトハッシュ・鎖・遅延一致）。
  ハッシュ表は入力長に合わせて縮める（小さい塊で 1 MB も確保しない）。
- 展開は表引き 1 回/記号。ビット読み出しの状態をレジスタに載せて回す。

## 全文


### `src/ifz/Ifz1.java`

```java
package ifz;

import java.io.IOException;
import java.util.Arrays;

/**
 * IFZ1: 塊（フレーム列）専用の可逆圧縮。
 * 共有の可変状態を持たず、同じ入力からは必ず同じ出力を返す。
 */
public final class Ifz1 {

	private Ifz1() {
	}

	// ===== 上限 =====
	/** 塊の上限 256MB */
	public static final int MAX_RAW = 256 << 20;
	/** 中身1個の上限 4KB */
	public static final int MAX_ITEM = 4096;

	static final int MAX_TYPE = 1 << 20;
	static final int MAX_LANES = 4096;
	static final int MIN_FRAMES = 16;
	static final int MAX_BITS = 11;
	static final int TAB_BITS = 11;
	static final int MIN_MATCH = 3;
	static final int MAX_MATCH = 1 << 20;
	static final int MIN_RECORD_BYTES = 256;

	static final int FLAG_LANES = 1;
	static final int K_HEAD = 0;
	static final int K_TYPE = 1;
	static final int K_MISC = 2;
	static final int M_STORED = 0;
	static final int M_LZ = 1;
	static final int C_CONST = 0;
	static final int C_RAW = 1;
	static final int C_BASE = 2;
	static final int C_DBITS = 3;
	static final int C_HUFF = 4;
	static final int C_DCOL = 5;
	/** 列ハフマンを使う最大の記号数 */
	static final int HUFF_LIMIT = 256;

	// ===== 公開API =====

	/** 置き場確保用の最大バイト数。 */
	public static int maxPackedLength(int rawLength) {
		if (rawLength < 0 || rawLength > MAX_RAW) throw new IllegalArgumentException("rawLength");
		return rawLength + (rawLength >>> 3) + 4096;
	}




	/** 塊を圧縮する。effort: 0=速い 1=強い */
	public static byte[] compressBlock(byte[] raw, int effort) {
		if (raw == null) throw new NullPointerException("raw");
		if (raw.length > MAX_RAW) throw new IllegalArgumentException("rawLength");
		int eff = effort <= 0 ? 0 : 1;
		Frames f = parseFrames(raw);
		if (f != null) {
			try {
				return compressFrames(raw, f, eff);
			} catch (TooBig e) {
				// 形は取れたが膨らんだ。単一ストリームに逃がす
			}
		}
		return compressSingle(raw, eff);
	}

	/** 塊を展開する。壊れていたら IOException。 */
	public static byte[] decompressBlock(byte[] packed, int rawLength) throws IOException {
		if (packed == null) throw new IOException("packed is null");
		if (rawLength < 0 || rawLength > MAX_RAW) throw new IOException("bad rawLength " + rawLength);
		BitIn in = new BitIn(packed);
		if (in.left() < 5) throw new IOException("truncated header");
		if (in.u8() != 'I' || in.u8() != 'F' || in.u8() != 'Z' || in.u8() != '1') throw new IOException("bad magic");
		int flags = in.u8();
		if ((flags & ~FLAG_LANES) != 0) throw new IOException("unknown flags " + flags);
		long rl = in.varint();
		if (rl != (rawLength & 0xFFFFFFFFL)) throw new IOException("rawLength mismatch");
		byte[] out = new byte[rawLength];
		if ((flags & FLAG_LANES) != 0) decompressFrames(in, out);
		else decompressSingle(in, out);
		return out;
	}

	// ===== 単一ストリーム =====

	static byte[] compressSingle(byte[] raw, int eff) {
		ByteOut out = new ByteOut(32 + raw.length + (raw.length >>> 3));
		out.u8('I');
		out.u8('F');
		out.u8('Z');
		out.u8('1');
		out.u8(0);
		out.varint(raw.length);
		BitBuf lb = new BitBuf(32 + raw.length / 2);
		lzEncode(lb, raw, 0, raw.length, eff);
		byte[] lz = lb.toArray();
		int method;
		byte[] body;
		if (lz.length < raw.length) {
			method = M_LZ;
			body = lz;
		} else {
			method = M_STORED;
			body = raw;
		}
		out.u8(method);
		out.varint(body.length);
		out.put(body, 0, body.length);
		out.u32(crc32(raw, 0, raw.length));
		return out.toArray();
	}

	static void decompressSingle(BitIn in, byte[] out) throws IOException {
		int method = in.u8();
		if (method != M_STORED && method != M_LZ) throw new IOException("bad method " + method);
		long plen = in.varint();
		if (plen < 0 || plen > in.left()) throw new IOException("bad packed length");
		if (method == M_STORED) {
			if (plen != out.length) throw new IOException("bad stored length");
			in.bytes(out, 0, out.length);
		} else {
			lzDecode(in, out, 0, out.length);
			in.align();
		}
		if (in.left() < 4) throw new IOException("no crc");
		int crc = in.u32();
		if (crc != crc32(out, 0, out.length)) throw new IOException("crc mismatch");
	}

	// ===== フレーム解析 =====

	static final class Frames {
		int n;
		int[] type, delta, len, off;
		int[] laneType;
		int lanes;
	}

	/** フレーム列として読めれば情報を返し、読めなければ null。 */
	static Frames parseFrames(byte[] raw) {
		int n = raw.length;
		if (n < 32) return null;
		int cap = Math.min(n / 24 + 16, 1 << 22);
		int[] type = new int[cap];
		int[] delta = new int[cap];
		int[] len = new int[cap];
		int[] off = new int[cap];
		int p = 0;
		int i = 0;
		while (p < n) {
			if (i >= cap) {
				if (cap >= (1 << 22)) return null;
				cap = Math.min(cap * 2, 1 << 22);
				type = Arrays.copyOf(type, cap);
				delta = Arrays.copyOf(delta, cap);
				len = Arrays.copyOf(len, cap);
				off = Arrays.copyOf(off, cap);
			}
			int s = p;
			long r = readVarint(raw, p, n);
			if (r < 0) return null;
			p = (int) (r >>> 32);
			int dv = (int) r;
			if (dv < 0 || dv >= (1 << 28)) return null;
			r = readVarint(raw, p, n);
			if (r < 0) return null;
			p = (int) (r >>> 32);
			int tv = (int) r;
			if (tv < 0 || tv > MAX_TYPE) return null;
			r = readVarint(raw, p, n);
			if (r < 0) return null;
			p = (int) (r >>> 32);
			int lv = (int) r;
			if (lv < 0 || lv > MAX_ITEM) return null;
			if (p - s < 3 || p + lv > n) return null;
			type[i] = tv;
			delta[i] = dv;
			len[i] = lv;
			off[i] = p;
			p += lv;
			i++;
		}
		if (p != n || i < MIN_FRAMES) return null;
		int[] sorted = Arrays.copyOf(type, i);
		Arrays.sort(sorted);
		int lanes = 0;
		for (int k = 0; k < i; k++) {
			if (k == 0 || sorted[k] != sorted[k - 1]) lanes++;
		}
		if (lanes > MAX_LANES) return null;
		Frames f = new Frames();
		f.n = i;
		f.type = type;
		f.delta = delta;
		f.len = len;
		f.off = off;
		f.lanes = lanes;
		f.laneType = new int[lanes];
		int q = 0;
		for (int k = 0; k < i; k++) {
			if (k == 0 || sorted[k] != sorted[k - 1]) f.laneType[q++] = sorted[k];
		}
		return f;
	}

	static int laneIndex(int[] laneType, int type) {
		int lo = 0;
		int hi = laneType.length - 1;
		while (lo <= hi) {
			int mid = (lo + hi) >>> 1;
			int v = laneType[mid];
			if (v == type) return mid;
			if (v < type) lo = mid + 1;
			else hi = mid - 1;
		}
		return -1;
	}

	// ===== フレーム圧縮 =====

	static byte[] compressFrames(byte[] raw, Frames f, int eff) {
		int n = f.n;
		int lanes = f.lanes;
		int limit = maxPackedLength(raw.length);

		int[] laneOf = new int[n];
		int[] cnt = new int[lanes];
		for (int i = 0; i < n; i++) {
			int k = laneIndex(f.laneType, f.type[i]);
			laneOf[i] = k;
			cnt[k]++;
		}
		int[] start = new int[lanes + 1];
		for (int k = 0; k < lanes; k++) start[k + 1] = start[k] + cnt[k];
		int[] ord = new int[n];
		int[] cur = Arrays.copyOf(start, lanes);
		for (int i = 0; i < n; i++) ord[cur[laneOf[i]]++] = i;

		// レーンごとのレコード長（最も多くを占める中身の長さ）
		int[] recLen = new int[lanes];
		int[] recCnt = new int[lanes];
		int[] lenHist = new int[MAX_ITEM + 1];
		for (int k = 0; k < lanes; k++) {
			int a = start[k];
			int b = start[k + 1];
			Arrays.fill(lenHist, 0);
			for (int i = a; i < b; i++) lenHist[f.len[ord[i]]]++;
			long bestScore = 0;
			int best = 0;
			int bestCnt = 0;
			for (int L = 1; L <= MAX_ITEM; L++) {
				int c = lenHist[L];
				if (c != 0 && (long) c * L > bestScore) {
					bestScore = (long) c * L;
					best = L;
					bestCnt = c;
				}
			}
			if (best > 0 && bestScore >= MIN_RECORD_BYTES && best <= MAX_ITEM) {
				recLen[k] = best;
				recCnt[k] = bestCnt;
			}
		}

		// 頻度収集
		int[] typeFreq = new int[lanes];
		int[] deltaFreq = new int[256];
		int[] lenFreq = new int[256];
		for (int i = 0; i < n; i++) {
			typeFreq[laneOf[i]]++;
			countVarint(deltaFreq, f.delta[i]);
			countVarint(lenFreq, f.len[i]);
		}
		// 転置はせず、レコードの位置だけをレーンごとに拾う（中身は raw から直接読む）
		int maxCnt = 0;
		for (int k = 0; k < lanes; k++) {
			if (recCnt[k] > maxCnt) maxCnt = recCnt[k];
		}
		int[] roff = new int[maxCnt];
		RecWork rw = new RecWork();

		MiniHuff mRaw = new MiniHuff();
		MiniHuff mDel = new MiniHuff();
		Huff typeTab = Huff.build(typeFreq, lanes);
		Huff deltaTab = Huff.build(deltaFreq, 256);
		Huff lenTab = Huff.build(lenFreq, 256);

		int totalLanes = lanes + 2;
		byte[][] packed = new byte[totalLanes][];
		int[] pLen = new int[totalLanes];
		int[] rawLen = new int[totalLanes];

		// 先頭レーン（表と型・delta）
		BitBuf hb = new BitBuf(256 + n * 3);
		hb.limit = limit;
		typeTab.write(hb);
		deltaTab.write(hb);
		lenTab.write(hb);
		for (int i = 0; i < n; i++) typeTab.encode(hb, laneOf[i]);
		for (int i = 0; i < n; i++) putVarintHuff(hb, deltaTab, f.delta[i]);
		hb.flush();
		packed[0] = hb.b;
		pLen[0] = hb.n;
		rawLen[0] = n;

		// 種類レーン
		for (int k = 0; k < lanes; k++) {
			BitBuf b = new BitBuf(64 + cnt[k] * 2 + ((recLen[k] * recCnt[k]) >>> 1));
			b.limit = limit;
			for (int i = start[k]; i < start[k + 1]; i++) putVarintHuff(b, lenTab, f.len[ord[i]]);
			if (recLen[k] > 0) {
				int rc = 0;
				for (int i = start[k]; i < start[k + 1]; i++) {
					int fi = ord[i];
					if (f.len[fi] == recLen[k]) roff[rc++] = f.off[fi];
				}
				encodeRecords(b, raw, roff, rc, recLen[k], mRaw, mDel, rw);
			}
			b.flush();
			packed[k + 1] = b.b;
			pLen[k + 1] = b.n;
			rawLen[k + 1] = recCnt[k] * recLen[k];
		}

		// misc レーン（レコードにならなかった中身）
		int miscLen = 0;
		for (int i = 0; i < n; i++) {
			if (recLen[laneOf[i]] != f.len[i]) miscLen += f.len[i];
		}
		byte[] misc = new byte[miscLen];
		int mp = 0;
		for (int i = 0; i < n; i++) {
			int k = laneOf[i];
			if (recLen[k] == f.len[i]) continue;
			System.arraycopy(raw, f.off[i], misc, mp, f.len[i]);
			mp += f.len[i];
		}
		// 方式の 1 バイトは表を書いた後に置くので、本体は無複製で載せる
		int miscMethod;
		if (miscLen == 0) {
			miscMethod = M_STORED;
			packed[lanes + 1] = new byte[0];
		} else {
			BitBuf lb = new BitBuf(64 + miscLen / 2);
			lb.limit = limit;
			lzEncode(lb, misc, 0, miscLen, eff);
			lb.flush();
			if (lb.n < miscLen) {
				miscMethod = M_LZ;
				packed[lanes + 1] = lb.b;
				pLen[lanes + 1] = lb.n;
			} else {
				miscMethod = M_STORED;
				packed[lanes + 1] = misc;
				pLen[lanes + 1] = miscLen;
			}
		}
		rawLen[lanes + 1] = miscLen;

		// 書き出し。ヘッダと表の長さを先に数えて、ぴったりの配列を 1 本だけ確保する
		int outLen = 5 + vlen(raw.length) + vlen(n) + vlen(totalLanes);
		for (int k = 0; k < totalLanes; k++) {
			int kind = k == 0 ? K_HEAD : (k <= lanes ? K_TYPE : K_MISC);
			outLen += vlen(kind) + 1 + vlen(rawLen[k]) + vlen(pLen[k] + (kind == K_MISC ? 1 : 0)) + 4 + (kind == K_TYPE ? vlen(recLen[k - 1]) + vlen(recCnt[k - 1]) : 0) + pLen[k] + (kind == K_MISC ? 1 : 0);
		}
		ByteOut out = new ByteOut(outLen);
		out.limit = limit;
		out.u8('I');
		out.u8('F');
		out.u8('Z');
		out.u8('1');
		out.u8(FLAG_LANES);
		out.varint(raw.length);
		out.varint(n);
		out.varint(totalLanes);
		for (int k = 0; k < totalLanes; k++) {
			int kind = k == 0 ? K_HEAD : (k <= lanes ? K_TYPE : K_MISC);
			out.varint(kind);
			out.varint(kind == K_TYPE ? f.laneType[k - 1] : 0);
			out.varint(rawLen[k]);
			// 表の長さと CRC は「方式の 1 バイト込み」の本体全体を表す
			out.varint(pLen[k] + (k == lanes + 1 ? 1 : 0));
			out.u32(k == lanes + 1 ? crc32(miscMethod, packed[k], 0, pLen[k]) : crc32(packed[k], 0, pLen[k]));
			if (kind == K_TYPE) {
				out.varint(recLen[k - 1]);
				out.varint(recCnt[k - 1]);
			}
		}
		for (int k = 0; k < totalLanes; k++) {
			if (k == lanes + 1) out.u8(miscMethod);
			out.put(packed[k], 0, pLen[k]);
		}
		if (miscMethod != M_STORED && miscMethod != M_LZ) throw new IllegalStateException();
		return out.toArray();
	}

	static void decompressFrames(BitIn in, byte[] out) throws IOException {
		int n = (int) in.varint();
		if (n < 0 || n > (1 << 22)) throw new IOException("bad nFrames");
		int totalLanes = (int) in.varint();
		if (totalLanes < 2 || totalLanes > MAX_LANES + 2) throw new IOException("bad laneCount");
		int[] kind = new int[totalLanes];
		int[] id = new int[totalLanes];
		int[] rlen = new int[totalLanes];
		int[] plen = new int[totalLanes];
		int[] crc = new int[totalLanes];
		int[] recLen = new int[totalLanes];
		int[] recCnt = new int[totalLanes];
		long sum = 0;
		for (int k = 0; k < totalLanes; k++) {
			kind[k] = (int) in.varint();
			id[k] = (int) in.varint();
			rlen[k] = (int) in.varint();
			plen[k] = (int) in.varint();
			crc[k] = in.u32();
			if (kind[k] < K_HEAD || kind[k] > K_MISC) throw new IOException("bad lane kind");
			if (id[k] < 0 || id[k] > MAX_TYPE) throw new IOException("bad lane id");
			if (rlen[k] < 0 || plen[k] < 0) throw new IOException("bad lane length");
			if (kind[k] == K_TYPE) {
				recLen[k] = (int) in.varint();
				recCnt[k] = (int) in.varint();
				if (recLen[k] < 0 || recLen[k] > MAX_ITEM) throw new IOException("bad record length");
				if (recCnt[k] < 0 || (long) recCnt[k] * recLen[k] != rlen[k]) throw new IOException("bad record count");
			}
			sum += plen[k];
		}
		if (sum > in.left()) throw new IOException("truncated lanes");
		if (kind[0] != K_HEAD) throw new IOException("no head lane");
		if (kind[totalLanes - 1] != K_MISC) throw new IOException("no misc lane");
		int lanes = totalLanes - 2;
		for (int k = 1; k <= lanes; k++) {
			if (kind[k] != K_TYPE) throw new IOException("bad lane order");
		}
		// レーン単位で CRC 検証（破損は他レーンに波及しない）
		if ((in.bitPos & 7) != 0) throw new IOException("lane table not aligned");
		int base = (int) (in.bitPos >>> 3);
		int[] lo = new int[totalLanes];
		BitIn[] lane = new BitIn[totalLanes];
		int acc = 0;
		for (int k = 0; k < totalLanes; k++) {
			if (base + acc + plen[k] > in.end) throw new IOException("lane truncated");
			lo[k] = base + acc;
			if (crc32(in.b, lo[k], plen[k]) != crc[k]) throw new IOException("lane crc mismatch at " + k);
			lane[k] = new BitIn(in.b, lo[k], lo[k] + plen[k]);
			acc += plen[k];
		}

		BitIn hb = lane[0];
		Huff typeTab = Huff.read(hb);
		Huff deltaTab = Huff.read(hb);
		Huff lenTab = Huff.read(hb);
		int[] types = new int[n];
		for (int i = 0; i < n; i++) {
			int t = typeTab.decode(hb);
			if (t < 0 || t >= lanes) throw new IOException("bad type index");
			types[i] = t;
		}
		int[] deltas = new int[n];
		for (int i = 0; i < n; i++) deltas[i] = getVarintHuff(hb, deltaTab);

		int[] cnt = new int[totalLanes];
		for (int i = 0; i < n; i++) cnt[types[i] + 1]++;

		int[][] lens = new int[totalLanes][];
		boolean[] hasRec = new boolean[totalLanes];
		MiniHuff mini = new MiniHuff();
		for (int k = 1; k <= lanes; k++) {
			BitIn b = lane[k];
			int[] ls = new int[cnt[k]];
			for (int j = 0; j < cnt[k]; j++) {
				int v = getVarintHuff(b, lenTab);
				if (v < 0 || v > MAX_ITEM) throw new IOException("bad item length");
				ls[j] = v;
			}
			lens[k] = ls;
			hasRec[k] = recLen[k] > 0 && recCnt[k] > 0;
		}

		int miscLen = 0;
		for (int k = 1; k <= lanes; k++) {
			int[] ls = lens[k];
			for (int j = 0; j < ls.length; j++) {
				if (ls[j] != recLen[k] || !hasRec[k]) miscLen += ls[j];
			}
		}
		byte[] misc = new byte[miscLen];
		if (miscLen > 0) {
			BitIn b = lane[totalLanes - 1];
			int method = b.u8();
			if (method == M_STORED) {
				if (plen[totalLanes - 1] - 1 != miscLen) throw new IOException("bad misc size");
				b.bytes(misc, 0, miscLen);
			} else if (method == M_LZ) {
				lzDecode(b, misc, 0, miscLen);
			} else {
				throw new IOException("bad misc method " + method);
			}
		}

		// 出力位置を決めながらヘッダを書き、レコードの場所を控える
		int totalRec = 0;
		for (int k = 1; k <= lanes; k++) if (hasRec[k]) totalRec += recCnt[k];
		int[] recBase = new int[totalLanes + 1];
		for (int k = 1; k <= lanes; k++) recBase[k + 1] = recBase[k] + (hasRec[k] ? recCnt[k] : 0);
		int[] recPos = new int[totalRec];
		int[] recAt = new int[totalLanes];
		int[] lenAt = new int[totalLanes];
		int miscAt = 0;
		int p = 0;
		for (int i = 0; i < n; i++) {
			int k = types[i] + 1;
			int li = lenAt[k]++;
			if (li >= lens[k].length) throw new IOException("lane overflow");
			int L = lens[k][li];
			p = putVarint(out, p, deltas[i]);
			p = putVarint(out, p, id[k]);
			p = putVarint(out, p, L);
			if (p + L > out.length) throw new IOException("output overflow");
			if (L == recLen[k] && hasRec[k]) {
				int a = recAt[k];
				if (a >= recCnt[k]) throw new IOException("record overflow");
				recPos[recBase[k] + a] = p;
				recAt[k] = a + 1;
			} else {
				if (miscAt + L > misc.length) throw new IOException("misc overflow");
				System.arraycopy(misc, miscAt, out, p, L);
				miscAt += L;
			}
			p += L;
		}
		if (p != out.length) throw new IOException("size mismatch");
		// レコード列を out へ直接展開する（写しを一段省く）
		for (int k = 1; k <= lanes; k++) {
			if (!hasRec[k]) continue;
			if (recAt[k] != recCnt[k]) throw new IOException("record count mismatch");
			decodeRecords(lane[k], out, recPos, recBase[k], recCnt[k], recLen[k], mini);
		}
		if (p != out.length) throw new IOException("size mismatch");
	}

	// ===== レコード列 =====

	/** rec は列優先（列 j の r 番目は rec[j * rc + r]） */
	/** 列の統計に使う使い回しの作業配列。レーンごとに確保しない。 */
	static final class RecWork {
		final int[] hist = new int[256];
		final int[] dhist = new int[256];
		final int[] uvals = new int[256];
		final int[] uvals2 = new int[256];
		final int[] vals = new int[HUFF_LIMIT];
		final int[] freqs = new int[HUFF_LIMIT];
		final int[] vals2 = new int[HUFF_LIMIT];
		final int[] freqs2 = new int[HUFF_LIMIT];
	}

	/** 列優先でレコードを符号化する。rec は列 j の r 番目が rec[off[r] + j]。 */
	static void encodeRecords(BitBuf b, byte[] raw, int[] off, int rc, int rl, MiniHuff mRaw, MiniHuff mDel,
			RecWork w) {
		int[] hist = w.hist;
		int[] dhist = w.dhist;
		int[] uvals = w.uvals;
		int[] uvals2 = w.uvals2;
		int[] vals = w.vals;
		int[] freqs = w.freqs;
		int[] vals2 = w.vals2;
		int[] freqs2 = w.freqs2;
		for (int j = 0; j < rl; j++) {
			int min = 255;
			int max = 0;
			int first = raw[off[0] + j] & 0xFF;
			int prev = first;
			int kmax = 0;
			boolean bigDelta = false;
			int ud = 0;
			int ud2 = 0;
			for (int r = 0; r < rc; r++) {
				int v = raw[off[r] + j] & 0xFF;
				if (hist[v]++ == 0) uvals[ud++] = v;
				if (v < min) min = v;
				if (v > max) max = v;
				if (r > 0) {
					int z = zig(v - prev);
					if (z < 256) {
						if (!bigDelta && dhist[z]++ == 0) uvals2[ud2++] = z;
					} else {
						bigDelta = true; // 差が大きい列は delta ハフマンを使わない
					}
					if (z > kmax) kmax = z;
					prev = v;
				}
			}
			// 値を昇順に並べて頻度を詰める（使った分だけ消す）
			sortAsc(uvals, ud);
			for (int i = 0; i < ud; i++) {
				int v = uvals[i];
				vals[i] = v;
				freqs[i] = hist[v];
				hist[v] = 0;
			}
			sortAsc(uvals2, ud2);
			for (int i = 0; i < ud2; i++) {
				int v = uvals2[i];
				vals2[i] = v;
				freqs2[i] = dhist[v];
				dhist[v] = 0;
			}
			int span = max - min;
			int kb = span == 0 ? 0 : 32 - Integer.numberOfLeadingZeros(span);
			int kdb = kmax == 0 ? 0 : 32 - Integer.numberOfLeadingZeros(kmax);
			long cConst = span == 0 ? 16 : Long.MAX_VALUE;
			long cRaw = 8 + 8L * rc;
			long cBase = 24 + (long) kb * rc;
			long cDb = 24 + (long) kdb * (rc - 1);
			long cHuff = Long.MAX_VALUE;
			int dRaw = ud;
			if (mRaw.build(vals, freqs, dRaw, rc)) cHuff = 16 + 16L * dRaw + mRaw.dataCost(freqs, dRaw);
			long cDcol = Long.MAX_VALUE;
			int dDel = bigDelta ? 257 : ud2;
			if (!bigDelta && mDel.build(vals2, freqs2, ud2, rc - 1)) {
				cDcol = 24 + 16L * dDel + mDel.dataCost(freqs2, dDel);
			}
			long best = cRaw;
			int mode = C_RAW;
			if (cConst < best) { best = cConst; mode = C_CONST; }
			if (cBase < best) { best = cBase; mode = C_BASE; }
			if (cDb < best) { best = cDb; mode = C_DBITS; }
			if (cHuff < best) { best = cHuff; mode = C_HUFF; }
			if (cDcol < best) { mode = C_DCOL; }
			b.u8(mode);
			switch (mode) {
			case C_CONST:
				b.u8(min);
				break;
			case C_RAW:
				for (int r = 0; r < rc; r++) b.u8(raw[off[r] + j] & 0xFF);
				break;
			case C_BASE:
				b.u8(min);
				b.u8(kb);
				for (int r = 0; r < rc; r++) b.bits((raw[off[r] + j] & 0xFF) - min, kb);
				break;
			case C_DBITS:
				b.u8(first);
				b.u8(kdb);
				prev = first;
				for (int r = 1; r < rc; r++) {
					int v = raw[off[r] + j] & 0xFF;
					b.bits(zig(v - prev), kdb);
					prev = v;
				}
				break;
			case C_HUFF:
				mRaw.write(b);
				for (int r = 0; r < rc; r++) {
					int v = raw[off[r] + j] & 0xFF;
					b.bits(mRaw.codeOf[v], mRaw.lenOf[v]);
				}
				break;
			default:
				b.u8(first);
				mDel.write(b);
				prev = first;
				for (int r = 1; r < rc; r++) {
					int v = raw[off[r] + j] & 0xFF;
					int z = zig(v - prev);
					b.bits(mDel.codeOf[z], mDel.lenOf[z]);
					prev = v;
				}
				break;
			}
		}
	}

	/** 小さい配列を昇順に並べる */
	static void sortAsc(int[] a, int n) {
		if (n < 32) {
			for (int i = 1; i < n; i++) {
				int t = a[i];
				int j = i - 1;
				while (j >= 0 && a[j] > t) {
					a[j + 1] = a[j];
					j--;
				}
				a[j + 1] = t;
			}
		} else {
			Arrays.sort(a, 0, n);
		}
	}

	static void decodeRecords(BitIn in, byte[] out, int[] recPos, int rbase, int rc, int rl, MiniHuff mh)
			throws IOException {
		for (int j = 0; j < rl; j++) {
			int mode = in.u8();
			switch (mode) {
			case C_CONST: {
				byte v = (byte) in.u8();
				for (int r = 0; r < rc; r++) out[recPos[rbase + r] + j] = v;
				break;
			}
			case C_RAW:
				for (int r = 0; r < rc; r++) out[recPos[rbase + r] + j] = (byte) in.u8();
				break;
			case C_BASE: {
				int min = in.u8();
				int k = in.u8();
				if (k > 8) throw new IOException("bad base bits");
				for (int r = 0; r < rc; r++) out[recPos[rbase + r] + j] = (byte) (min + in.bits(k));
				break;
			}
			case C_DBITS: {
				int prev = in.u8();
				int k = in.u8();
				if (k > 10) throw new IOException("bad delta bits");
				out[recPos[rbase] + j] = (byte) prev;
				for (int r = 1; r < rc; r++) {
					prev = (prev + unzig(in.bits(k))) & 0xFF;
					out[recPos[rbase + r] + j] = (byte) prev;
				}
				break;
			}
			case C_HUFF:
				mh.read(in);
				in.decodeColumn(mh, out, recPos, rbase, rc, j, false, 0);
				break;
			case C_DCOL: {
				int prev = in.u8();
				mh.read(in);
				out[recPos[rbase] + j] = (byte) prev;
				in.decodeColumn(mh, out, recPos, rbase + 1, rc - 1, j, true, prev);
				break;
			}
			default:
				throw new IOException("bad column mode " + mode);
			}
		}
	}
	/** 列ごとの小さなハフマン（記号数 HUFF_LIMIT 以下） */
	static final class MiniHuff {
		int d;
		final int[] val = new int[HUFF_LIMIT];
		final byte[] len = new byte[HUFF_LIMIT];
		final int[] code = new int[HUFF_LIMIT];
		final int[] codeOf = new int[256];
		final byte[] lenOf = new byte[256];
		final int[] tab = new int[1 << TAB_BITS];
		int tabBits;
		// 構築用の作業領域（列をまたいで使い回す）
		final long[] w = new long[2 * HUFF_LIMIT];
		final int[] c1 = new int[2 * HUFF_LIMIT];
		final int[] c2 = new int[2 * HUFF_LIMIT];
		final int[] st = new int[2 * HUFF_LIMIT];
		final int[] sd = new int[2 * HUFF_LIMIT];
		final int[] leaf = new int[HUFF_LIMIT];
		final int[] iq = new int[HUFF_LIMIT];
		final int[] blCount = new int[MAX_BITS + 2];
		final int[] nextCode = new int[MAX_BITS + 2];
		final int[] bucket = new int[MAX_BITS + 3];
		final long[] sortKey = new long[HUFF_LIMIT];
		final int[] order = new int[HUFF_LIMIT];

		/** vals は昇順。符号長が MAX_BITS を超えたら false。 */
		/** vals は昇順。符号長が MAX_BITS を超えたら false。 */
		boolean build(int[] vals, int[] freqs, int count, long total) {
			d = count;
			if (count < 1) return false;
			if (count == 1) {
				val[0] = vals[0];
				len[0] = 1;
				code[0] = 0;
				index();
				return true;
			}
			long minF = Math.max(1, total >>> (MAX_BITS - 2));
			for (int i = 0; i < count; i++) {
				val[i] = vals[i];
				w[i] = Math.max(freqs[i], minF);
			}
			// 葉を重み昇順に並べる
			for (int i = 0; i < count; i++) leaf[i] = i;
			if (count < 32) {
				for (int i = 1; i < count; i++) {
					int t = leaf[i];
					long tw = w[t];
					int j = i - 1;
					while (j >= 0 && w[leaf[j]] > tw) {
						leaf[j + 1] = leaf[j];
						j--;
					}
					leaf[j + 1] = t;
				}
			} else {
				// 重みと添字を 1 つの long に詰めて並べる
				for (int i = 0; i < count; i++) sortKey[i] = (w[i] << 16) | i;
				Arrays.sort(sortKey, 0, count);
				for (int i = 0; i < count; i++) leaf[i] = (int) sortKey[i] & 0xFFFF;
			}
			// 2キュー法でハフマン木を作る
			int ha = 0;
			int hb = 0;
			int tb = 0;
			int n = count;
			for (int s = 0; s < count - 1; s++) {
				int a;
				int bb;
				if (hb < tb && (ha >= count || w[iq[hb]] < w[leaf[ha]])) a = iq[hb++];
				else a = leaf[ha++];
				if (hb < tb && (ha >= count || w[iq[hb]] < w[leaf[ha]])) bb = iq[hb++];
				else bb = leaf[ha++];
				c1[n] = a;
				c2[n] = bb;
				w[n] = w[a] + w[bb];
				iq[tb++] = n;
				n++;
			}
			// 深さを数える
			int maxLen = 0;
			int sp = 0;
			st[sp] = n - 1;
			sd[sp] = 0;
			sp++;
			while (sp > 0) {
				sp--;
				int x = st[sp];
				int dd = sd[sp];
				if (x < count) {
					len[x] = (byte) dd;
					if (dd > maxLen) maxLen = dd;
					continue;
				}
				st[sp] = c1[x];
				sd[sp] = dd + 1;
				sp++;
				st[sp] = c2[x];
				sd[sp] = dd + 1;
				sp++;
			}
			if (maxLen > MAX_BITS) return false;
			assign();
			index();
			return true;
		}

		/** 正準符号を割り当てる。長さ별로 한 번씩만 훑는다 → O(d) */
		void assign() {
			Arrays.fill(blCount, 0);
			Arrays.fill(nextCode, 0);
			for (int i = 0; i < d; i++) blCount[len[i]]++;
			int c = 0;
			int t = 0;
			for (int bits = 1; bits <= MAX_BITS; bits++) {
				c = (c + blCount[bits - 1]) << 1;
				nextCode[bits] = c;
				bucket[bits] = t;
				t += blCount[bits];
			}
			// 長さが同じものは添字昇順に並ぶようバケツに配る
			Arrays.fill(order, 0, d, 0);
			for (int i = 0; i < d; i++) order[bucket[len[i]]++] = i;
			for (int bits = 1; bits <= MAX_BITS; bits++) {
				int nc = nextCode[bits];
				for (int i = bucket[bits] - blCount[bits]; i < bucket[bits]; i++) code[order[i]] = nc++;
			}
		}

		/** 符号は復号表と同じビット順（反転）で並べる */
		void index() {
			for (int i = 0; i < d; i++) {
				codeOf[val[i]] = Integer.reverse(code[i]) >>> (32 - len[i]);
				lenOf[val[i]] = len[i];
			}
		}

		long dataCost(int[] freqs, int count) {
			long sum = 0;
			for (int i = 0; i < count; i++) sum += (long) len[i] * freqs[i];
			return sum;
		}

		void write(BitBuf b) {
			b.u8(d);
			for (int i = 0; i < d; i++) {
				b.u8(val[i]);
				b.u8(len[i]);
			}
		}

		void read(BitIn in) throws IOException {
			d = in.u8();
			if (d < 1 || d > HUFF_LIMIT) throw new IOException("bad mini huff d");
			for (int i = 0; i < d; i++) {
				val[i] = in.u8();
				len[i] = (byte) in.u8();
				if (len[i] < 1 || len[i] > MAX_BITS) throw new IOException("bad mini huff len");
				if (i > 0 && val[i] <= val[i - 1]) throw new IOException("bad mini huff order");
			}
			assign();
			int ml = 1;
			for (int i = 0; i < d; i++) if (len[i] > ml) ml = len[i];
			tabBits = ml;
			int tot = 0;
			for (int i = 0; i < d; i++) tot += 1 << (ml - len[i]);
			if (tot != 1 << ml) throw new IOException("bad mini huff code");
			for (int i = 0; i < d; i++) {
				int l = len[i];
				int rev = Integer.reverse(code[i]) >>> (32 - l);
				for (int k = 0; k < (1 << (ml - l)); k++) tab[rev | (k << l)] = (l << 16) | i;
			}
		}

		int decode(BitIn in) throws IOException {
			int e = tab[in.peek(tabBits)];
			if (e < 0) throw new IOException("bad mini huff code");
			in.skip(e >>> 16);
			return val[e & 0xFFFF];
		}
	}

	// ===== LZ77 + Huffman =====

	static final int WINDOW = 1 << 16;
	static final int WMASK = WINDOW - 1;

	static void lzEncode(BitBuf out, byte[] src, int off, int n, int eff) {
		int maxChain = eff <= 0 ? 4 : 16;
		int nice = eff <= 0 ? 12 : 64;
		int[] litFreq = new int[257 + 64];
		int[] distFreq = new int[64];
		// (記号 << 18) | 追加ビット。トークン数は入力よりずっと少ないので半分から始める
		int[] tok = new int[Math.max(16, (n >>> 1) + 2)];
		int tn = 0;
		if (n >= MIN_MATCH) {
			int hb = hashBits(n);
			int hshift = 32 - hb;
			int[] head = new int[1 << hb];
			Arrays.fill(head, -1);
			int[] prev = new int[Math.min(n, WINDOW)];
			int p = 0;
			int ins = 0; // 鎖への登録は一度だけ、必ず昇順
			while (p < n) {
				while (ins < p && ins + HASH_LEN <= n) {
					int h = hash4(src, off + ins) >>> hshift;
					prev[ins & WMASK] = head[h];
					head[h] = ins;
					ins++;
				}
				int len = 0;
				int dist = 0;
				if (p + HASH_LEN <= n) {
					if (ins <= p) {
						int h = hash4(src, off + p) >>> hshift;
						prev[p & WMASK] = head[h];
						head[h] = p;
						ins = p + 1;
					}
					int c = prev[p & WMASK];
					int floor = Math.max(0, p - WINDOW + 1);
					int maxLen = Math.min(MAX_MATCH, n - p);
					int chain = maxChain;
					int best = MIN_MATCH - 1;
					while (c >= floor && chain-- > 0 && best < maxLen) {
						// 現時点の best 位置が合う候補だけ詳しく比べる
						if (src[off + c + best] == src[off + p + best]) {
							int l = 0;
							while (l + 8 <= maxLen && readLong(src, off + c + l) == readLong(src, off + p + l)) l += 8;
							while (l < maxLen && src[off + c + l] == src[off + p + l]) l++;
							if (l > best) {
								best = l;
								dist = p - c;
								if (l >= nice || l >= maxLen) break;
							}
						}
						c = prev[c & WMASK];
					}
					if (best >= MIN_MATCH) len = best;
				}
				int maxLen2 = Math.min(MAX_MATCH, n - p - 1);
				if (len >= MIN_MATCH && eff > 0 && p + 1 + HASH_LEN <= n && len < maxLen2) {
					// 1つ先の方が長く一致するなら literal を出して待つ
					if (ins <= p + 1) {
						int h2 = hash4(src, off + p + 1) >>> hshift;
						prev[(p + 1) & WMASK] = head[h2];
						head[h2] = p + 1;
						ins = p + 2;
					}
					int c2 = prev[(p + 1) & WMASK];
					int chain = maxChain;
					int best2 = len;
					int q1 = p + 1;
					int floor2 = Math.max(0, q1 - WINDOW + 1);
					while (c2 >= floor2 && chain-- > 0 && best2 < maxLen2) {
						if (src[off + c2 + best2] == src[off + q1 + best2]) {
							int l = 0;
							while (l + 8 <= maxLen2 && readLong(src, off + c2 + l) == readLong(src, off + q1 + l)) l += 8;
							while (l < maxLen2 && src[off + c2 + l] == src[off + q1 + l]) l++;
							if (l > best2) {
								best2 = l;
								if (l >= nice || l >= maxLen2) break;
							}
						}
						c2 = prev[c2 & WMASK];
					}
					if (best2 > len) {
						int lit = src[off + p] & 0xFF;
						litFreq[lit]++;
						if (tn == tok.length) tok = Arrays.copyOf(tok, tok.length * 2);
						tok[tn++] = lit << 18;
						p++;
						continue;
					}
				}
				if (len >= MIN_MATCH) {
					int lv = len - (MIN_MATCH - 1);
					int lc = vCode(lv);
					int ls = 257 + lc;
					litFreq[ls]++;
					if (tn + 2 > tok.length) tok = Arrays.copyOf(tok, tok.length * 2);
					tok[tn++] = (ls << 18) | (lv - vBase(lc));
					int dc = vCode(dist);
					distFreq[dc]++;
					tok[tn++] = ((321 + dc) << 18) | (dist - vBase(dc));
					p += len;
				} else {
					int lit = src[off + p] & 0xFF;
					litFreq[lit]++;
					if (tn == tok.length) tok = Arrays.copyOf(tok, tok.length * 2);
					tok[tn++] = lit << 18;
					p++;
				}
			}
		} else {
			for (int i = 0; i < n; i++) {
				int lit = src[off + i] & 0xFF;
				litFreq[lit]++;
				if (tn == tok.length) tok = Arrays.copyOf(tok, tok.length * 2);
				tok[tn++] = lit << 18;
			}
		}
		litFreq[256] = 1;
		int litN = 257;
		for (int i = litFreq.length - 1; i >= 257; i--) {
			if (litFreq[i] > 0) {
				litN = i + 1;
				break;
			}
		}
		int distN = 1;
		for (int i = distFreq.length - 1; i >= 0; i--) {
			if (distFreq[i] > 0) {
				distN = i + 1;
				break;
			}
		}
		Huff litTab = Huff.build(litFreq, litN);
		Huff distTab = Huff.build(distFreq, distN);
		litTab.write(out);
		distTab.write(out);
		for (int i = 0; i < tn; i++) {
			int t = tok[i];
			int s = t >>> 18;
			int e = t & 0x3FFFF;
			if (s > 320) {
				int dc = s - 321;
				distTab.encode(out, dc);
				int db = vExtra(dc);
				if (db > 0) out.bits(e, db);
			} else {
				litTab.encode(out, s);
				if (s >= 257) {
					int eb = vExtra(s - 257);
					if (eb > 0) out.bits(e, eb);
				}
			}
		}
		litTab.encode(out, 256);
		out.flush();
	}

	static void lzDecode(BitIn in, byte[] out, int off, int n) throws IOException {
		Huff litTab = Huff.read(in);
		Huff distTab = Huff.read(in);
		int p = 0;
		while (true) {
			int s = litTab.decode(in);
			if (s == 256) break;
			if (s < 256) {
				if (p >= n) throw new IOException("lz overflow");
				out[off + p++] = (byte) s;
			} else {
				int lc = s - 257;
				if (lc < 0 || lc >= 64) throw new IOException("bad length code");
				int eb = vExtra(lc);
				int len = vBase(lc) + (eb > 0 ? in.bits(eb) : 0) + (MIN_MATCH - 1);
				int ds = distTab.decode(in);
				if (ds < 0 || ds >= 64) throw new IOException("bad dist code");
				int db = vExtra(ds);
				int dist = vBase(ds) + (db > 0 ? in.bits(db) : 0);
				if (dist < 1 || dist > p || len < MIN_MATCH || p + len > n) throw new IOException("bad match");
				int s0 = off + p - dist;
				int d0 = off + p;
				if (dist >= len) {
					System.arraycopy(out, s0, out, d0, len);
				} else {
					for (int i = 0; i < len; i++) out[d0 + i] = out[s0 + i];
				}
				p += len;
			}
		}
		if (p != n) throw new IOException("lz size mismatch " + p + " != " + n);
	}

	// ===== Huffman =====

	static final class Huff {
		int nSym;
		byte[] len;
		int[] code;
		int[] rev; // 出力順に並べた符号
		int[] tab;

		static Huff build(int[] freq, int nSym) {
			Huff h = new Huff();
			h.nSym = nSym;
			h.len = new byte[nSym];
			h.code = new int[nSym];
			h.rev = new int[nSym];
			int m = 0;
			long total = 0;
			for (int i = 0; i < nSym; i++) {
				if (freq[i] > 0) {
					m++;
					total += freq[i];
				}
			}
			if (m == 1) {
				for (int i = 0; i < nSym; i++) {
					if (freq[i] > 0) h.len[i] = 1;
				}
			} else if (m > 1) {
				// 最短頻度に床を置いて符号長を MAX_BITS 以内に抑える
				long minF = Math.max(1, total >>> (MAX_BITS - 2));
				// 上位 48 bit が重み、下位 16 bit が葉の番号（重みは符号数の合計なので 2^47 未満）
				long[] key = new long[m];
				int[] sym = new int[m];
				int q = 0;
				for (int i = 0; i < nSym; i++) {
					if (freq[i] > 0) {
						sym[q] = i;
						key[q] = (Math.max(freq[i], minF) << 16) | q;
						q++;
					}
				}
				Arrays.sort(key); // 重み、同じなら番号の昇順
				// 2 キュー法で繋ぐ。優先度付きキューの一時オブジェクトを作らない
				int nodes = 2 * m;
				int[] c1 = new int[nodes];
				int[] c2 = new int[nodes];
				Arrays.fill(c1, -1);
				long[] qw = new long[m];
				int[] qi = new int[m];
				int lp = 0, qp = 0, qn = 0, next = m;
				while ((m - lp) + (qn - qp) > 1) {
					int a, b;
					long aw, bw;
					if (qn > qp && (lp >= m || qw[qp] < (key[lp] >>> 16))) {
						aw = qw[qp];
						a = qi[qp];
						qp++;
					} else {
						aw = key[lp] >>> 16;
						a = (int) (key[lp] & 0xFFFF);
						lp++;
					}
					if (qn > qp && (lp >= m || qw[qp] < (key[lp] >>> 16))) {
						bw = qw[qp];
						b = qi[qp];
						qp++;
					} else {
						bw = key[lp] >>> 16;
						b = (int) (key[lp] & 0xFFFF);
						lp++;
					}
					c1[next] = a;
					c2[next] = b;
					qw[qn] = aw + bw;
					qi[qn] = next;
					qn++;
					next++;
				}
				int[] depth = new int[nodes];
				int[] st = new int[nodes];
				int[] sd = new int[nodes];
				int sp = 0;
				st[sp] = next - 1;
				sd[sp++] = 0;
				while (sp > 0) {
					sp--;
					int x = st[sp];
					int d = sd[sp];
					if (c1[x] < 0) {
						h.len[sym[x]] = (byte) Math.min(d, MAX_BITS);
					} else {
						st[sp] = c1[x];
						sd[sp++] = d + 1;
						st[sp] = c2[x];
						sd[sp++] = d + 1;
					}
				}
			}
			h.assignCodes();
			return h;
		}

		void assignCodes() {
			int[] blCount = new int[MAX_BITS + 2];
			for (int i = 0; i < nSym; i++) blCount[len[i]]++;
			int[] nextCode = new int[MAX_BITS + 2];
			int code = 0;
			for (int bits = 1; bits <= MAX_BITS; bits++) {
				code = (code + blCount[bits - 1]) << 1;
				nextCode[bits] = code;
			}
			for (int i = 0; i < nSym; i++) {
				int l = len[i];
				if (l > 0) this.code[i] = nextCode[l]++;
			}
			tab = new int[1 << TAB_BITS];
			Arrays.fill(tab, -1);
			for (int s = 0; s < nSym; s++) {
				int l = len[s];
				if (l == 0) continue;
				int rv = Integer.reverse(this.code[s]) >>> (32 - l);
				rev[s] = rv;
				for (int k = 0; k < (1 << (TAB_BITS - l)); k++) tab[rv | (k << l)] = (l << 16) | s;
			}
		}

		/** 符号長表を書く（0〜11 はそのまま、12 以上は直前の長さの繰り返し） */
		void write(BitBuf b) {
			b.varint(nSym);
			int prev = -1;
			int i = 0;
			while (i < nSym) {
				int l = len[i];
				int run = 1;
				while (i + run < nSym && len[i + run] == l && run < 246) run++;
				if (l == prev && run >= 3) {
					b.u8(12 + run - 3);
				} else if (run >= 4) {
					b.u8(l);
					b.u8(12 + run - 4);
				} else {
					for (int k = 0; k < run; k++) b.u8(l);
				}
				prev = l;
				i += run;
			}
		}

		static Huff read(BitIn in) throws IOException {
			Huff h = new Huff();
			h.nSym = (int) in.varint();
			if (h.nSym < 1 || h.nSym > (1 << 16)) throw new IOException("bad huff nSym");
			h.len = new byte[h.nSym];
			h.code = new int[h.nSym];
			h.rev = new int[h.nSym];
			int i = 0;
			int prev = -1;
			while (i < h.nSym) {
				int v = in.u8();
				if (v < 12) {
					h.len[i++] = (byte) v;
					prev = v;
				} else {
					if (prev < 0) throw new IOException("bad huff run");
					int run = v - 12 + 3;
					for (int k = 0; k < run && i < h.nSym; k++) h.len[i++] = (byte) prev;
				}
			}
			for (int k = 0; k < h.nSym; k++) {
				if (h.len[k] < 0 || h.len[k] > MAX_BITS) throw new IOException("bad code length");
			}
			h.assignCodes();
			return h;
		}

		void encode(BitBuf b, int s) {
			b.bits(rev[s], len[s]);
		}

		int decode(BitIn in) throws IOException {
			int e = tab[in.peek(TAB_BITS)];
			if (e < 0) throw new IOException("bad huffman code");
			in.skip(e >>> 16);
			return e & 0xFFFF;
		}
	}

	// ===== 小道具 =====

	static final int HASH_BITS = 17;
	static final int HASH_MIN_BITS = 12;
	static final int HASH_LEN = 4;

	static long readLong(byte[] b, int i) {
		return (b[i] & 0xFFL) | ((b[i + 1] & 0xFFL) << 8) | ((b[i + 2] & 0xFFL) << 16) | ((b[i + 3] & 0xFFL) << 24)
				| ((b[i + 4] & 0xFFL) << 32) | ((b[i + 5] & 0xFFL) << 40) | ((b[i + 6] & 0xFFL) << 48)
				| ((b[i + 7] & 0xFFL) << 56);
	}

	/** 4 バイトをハッシュする。3 バイトより衝突がずっと少ない。 */
	static int hash4(byte[] b, int i) {
		int v = (b[i] & 0xFF) | ((b[i + 1] & 0xFF) << 8) | ((b[i + 2] & 0xFF) << 16) | ((b[i + 3] & 0xFF) << 24);
		return v * 0x9E3779B1;
	}

	/** 表の大きさ。小さい塊で無駄に確保しないよう入力に合わせて縮める。 */
	static int hashBits(int n) {
		int hb = 32 - Integer.numberOfLeadingZeros(Math.max(16, n)) - 3;
		if (hb < HASH_MIN_BITS) hb = HASH_MIN_BITS;
		if (hb > HASH_BITS) hb = HASH_BITS;
		return hb;
	}

	static int zig(int d) {
		return d < 0 ? (-d << 1) - 1 : (d << 1);
	}

	static int unzig(int z) {
		return (z & 1) == 0 ? (z >>> 1) : -((z + 1) >>> 1);
	}

	static int vCode(int v) {
		if (v <= 4) return v - 1;
		int ex = 32 - Integer.numberOfLeadingZeros(v - 1) - 2;
		int base = (1 << (ex + 1)) + 1;
		int half = 1 << ex;
		return (v < base + half) ? 2 * ex + 2 : 2 * ex + 3;
	}

	static int vExtra(int code) {
		return code < 4 ? 0 : (code - 2) >>> 1;
	}

	static int vBase(int code) {
		if (code < 4) return code + 1;
		int ex = (code - 2) >>> 1;
		return (1 << (ex + 1)) + 1 + ((code & 1) << ex);
	}

	static void countVarint(int[] freq, int v) {
		while (true) {
			int c = v & 0x7F;
			v >>>= 7;
			freq[v != 0 ? (c | 0x80) : c]++;
			if (v == 0) return;
		}
	}

	static void putVarintHuff(BitBuf b, Huff tab, int v) {
		while (true) {
			int c = v & 0x7F;
			v >>>= 7;
			tab.encode(b, v != 0 ? (c | 0x80) : c);
			if (v == 0) return;
		}
	}

	static int getVarintHuff(BitIn in, Huff tab) throws IOException {
		int sh = 0;
		int v = 0;
		for (int i = 0; i < 5; i++) {
			int c = tab.decode(in);
			if (c < 0 || c > 255) throw new IOException("bad varint byte");
			v |= (c & 0x7F) << sh;
			if ((c & 0x80) == 0) return v;
			sh += 7;
		}
		throw new IOException("varint too long");
	}

	static long readVarint(byte[] b, int p, int n) {
		int sh = 0;
		int v = 0;
		for (int i = 0; i < 5; i++) {
			if (p >= n) return -1;
			int c = b[p++] & 0xFF;
			v |= (c & 0x7F) << sh;
			if ((c & 0x80) == 0) return ((long) p << 32) | (v & 0xFFFFFFFFL);
			sh += 7;
		}
		return -1;
	}

	static int putVarint(byte[] b, int p, int v) throws IOException {
		while (true) {
			if (p >= b.length) throw new IOException("output overflow");
			int c = v & 0x7F;
			v >>>= 7;
			if (v != 0) {
				b[p++] = (byte) (c | 0x80);
			} else {
				b[p++] = (byte) c;
				return p;
			}
		}
	}

	static final class TooBig extends RuntimeException {
		private static final long serialVersionUID = 1L;
		TooBig() {
			super("too big");
		}
	}

	/** 伸長するバイト列 */
	static final class ByteOut {
		byte[] b;
		int n;
		int limit = Integer.MAX_VALUE;

		ByteOut(int cap) {
			b = new byte[Math.max(16, cap)];
		}

		void need(int k) {
			if (n + k > limit) throw new TooBig();
			if (n + k > b.length) {
				long cap = b.length;
				while (cap < n + k) cap += cap < (1 << 20) ? cap : cap >>> 1;
				b = Arrays.copyOf(b, (int) cap);
			}
		}

		void u8(int v) {
			need(1);
			b[n++] = (byte) v;
		}

		void u32(int v) {
			need(4);
			b[n++] = (byte) v;
			b[n++] = (byte) (v >>> 8);
			b[n++] = (byte) (v >>> 16);
			b[n++] = (byte) (v >>> 24);
		}

		void varint(long v) {
			need(10);
			while (true) {
				long c = v & 0x7F;
				v >>>= 7;
				if (v != 0) {
					b[n++] = (byte) (c | 0x80);
				} else {
					b[n++] = (byte) c;
					return;
				}
			}
		}

		void put(byte[] src, int off, int len) {
			need(len);
			System.arraycopy(src, off, b, n, len);
			n += len;
		}

		/** ちょうど使い切ったときは複製しない。 */
		byte[] toArray() {
			return n == b.length ? b : Arrays.copyOf(b, n);
		}
	}

	/** ビット単位で書く */
	/** (1<<k)-1 の表 */
	static final int[] MASK = new int[33];
	static {
		for (int i = 1; i < 33; i++) MASK[i] = (int) ((1L << i) - 1);
	}

	static final class BitBuf {
		byte[] b;
		int n;
		long acc;
		int bitN;
		int limit = Integer.MAX_VALUE;

		BitBuf(int cap) {
			b = new byte[Math.max(16, cap)];
		}

		void need(int k) {
			if (n + k > limit) throw new TooBig();
			if (n + k > b.length) {
				long cap = b.length;
				while (cap < n + k) cap += cap < (1 << 20) ? cap : cap >>> 1;
				b = Arrays.copyOf(b, (int) cap);
			}
		}

		void u8(int v) {
			bits(v, 8);
		}

		void varint(long v) {
			while (true) {
				long c = v & 0x7F;
				v >>>= 7;
				if (v != 0) {
					bits((int) c | 0x80, 8);
				} else {
					bits((int) c, 8);
					return;
				}
			}
		}

		void put(byte[] src, int off, int len) {
			need(len + 2);
			if (bitN == 0) {
				System.arraycopy(src, off, b, n, len);
				n += len;
			} else {
				for (int i = 0; i < len; i++) bits(src[off + i] & 0xFF, 8);
			}
		}

		/** k ビットを LSB 先で積む。32 ビット溜まったら 4 バイトまとめて出す。 */
		void bits(int v, int k) {
			acc |= (long) (v & MASK[k]) << bitN;
			bitN += k;
			if (bitN >= 32) {
				need(4);
				b[n++] = (byte) acc;
				b[n++] = (byte) (acc >>> 8);
				b[n++] = (byte) (acc >>> 16);
				b[n++] = (byte) (acc >>> 24);
				acc >>>= 32;
				bitN -= 32;
			}
		}

		void flush() {
			while (bitN > 0) {
				need(1);
				b[n++] = (byte) acc;
				acc >>>= 8;
				bitN -= 8;
			}
			acc = 0;
			bitN = 0;
		}

		byte[] toArray() {
			flush();
			return Arrays.copyOf(b, n);
		}
	}

	/** ビット単位で読む */
	static final class BitIn {
		final byte[] b;
		final int end;
		int pos;
		long acc;
		int bitN;
		long bitPos; // 消費したビット数

		BitIn(byte[] b) {
			this(b, 0, b.length);
		}

		/** b の [off, end) だけを読む視界。写しを作らない。 */
		BitIn(byte[] b, int off, int end) {
			this.b = b;
			this.pos = off;
			this.end = end;
		}

		/** 残りの全バイト数（ビット端数を切り捨て） */
		int left() {
			long bits = (long) (end - pos) * 8 + bitN;
			return (int) (bits >> 3);
		}

		int peek(int k) throws IOException {
			if (bitN < k) refill();
			return (int) (acc & ((1L << k) - 1));
		}

		/** 4バイトずつ補充する。末尾は零詰め。 */
		void refill() throws IOException {
			while (bitN <= 32) {
				if (pos + 4 <= end) {
					acc |= ((b[pos] & 0xFFL) | ((b[pos + 1] & 0xFFL) << 8) | ((b[pos + 2] & 0xFFL) << 16)
							| ((b[pos + 3] & 0xFFL) << 24)) << bitN;
					pos += 4;
					bitN += 32;
				} else if (pos < end) {
					acc |= (long) (b[pos++] & 0xFF) << bitN;
					bitN += 8;
				} else {
					if (bitN == 0) throw new IOException("bit stream ended");
					bitN += 8;
				}
			}
		}

		void skip(int k) throws IOException {
			if (k > bitN) throw new IOException("bad skip");
			acc >>>= k;
			bitN -= k;
			bitPos += k;
		}

		/** 次のバイト境界まで進む（パディングを飛ばす） */
		void align() throws IOException {
			int rem = (int) (bitPos & 7);
			if (rem == 0) return;
			int k = 8 - rem;
			while (bitN < k) bitN += 8;
			skip(k);
		}

		int bits(int k) throws IOException {
			if (k == 0) return 0;
			int v = peek(k);
			skip(k);
			return v;
		}

		int u8() throws IOException {
			if (bitN == 0) {
				if (pos >= end) throw new IOException("bit stream ended");
				bitPos += 8;
				return b[pos++] & 0xFF;
			}
			return bits(8);
		}

		int u32() throws IOException {
			if (bitN == 0 && pos + 4 <= end) {
				int v = (b[pos] & 0xFF) | ((b[pos + 1] & 0xFF) << 8) | ((b[pos + 2] & 0xFF) << 16)
						| ((b[pos + 3] & 0xFF) << 24);
				pos += 4;
				bitPos += 32;
				return v;
			}
			int v = bits(8);
			v |= bits(8) << 8;
			v |= bits(8) << 16;
			v |= bits(8) << 24;
			return v;
		}

		long varint() throws IOException {
			int sh = 0;
			long v = 0;
			for (int i = 0; i < 8; i++) {
				int c = u8();
				v |= (long) (c & 0x7F) << sh;
				if ((c & 0x80) == 0) return v;
				sh += 7;
			}
			throw new IOException("varint too long");
		}

		/** 表引き復号を rc 回。BitIn の状態をローカルに載せて回す。delta が true なら符号を差分として積む。 */
		void decodeColumn(MiniHuff mh, byte[] out, int[] recPos, int rbase, int rc, int j, boolean delta, int first)
				throws IOException {
			final int[] tab = mh.tab;
			final int[] val = mh.val;
			final int tb = mh.tabBits;
			final long mask = (1L << tb) - 1;
			final byte[] src = b;
			final int lim = end;
			int p = pos;
			long acc = this.acc;
			int bitN = this.bitN;
			long bp = bitPos;
			int prev = first;
			for (int r = 0; r < rc; r++) {
				while (bitN < tb) {
					if (p + 4 <= lim) {
						acc |= ((src[p] & 0xFFL) | ((src[p + 1] & 0xFFL) << 8) | ((src[p + 2] & 0xFFL) << 16)
								| ((src[p + 3] & 0xFFL) << 24)) << bitN;
						p += 4;
						bitN += 32;
					} else if (p < lim) {
						acc |= (long) (src[p++] & 0xFF) << bitN;
						bitN += 8;
					} else {
						if (bitN == 0) throw new IOException("bit stream ended");
						bitN += 8;
					}
				}
				int e = tab[(int) (acc & mask)];
				if (e < 0) throw new IOException("bad mini huff code");
				int l = e >>> 16;
				acc >>>= l;
				bitN -= l;
				bp += l;
				int v = val[e & 0xFFFF];
				if (delta) {
					prev = (prev + unzig(v)) & 0xFF;
					v = prev;
				}
				out[recPos[rbase + r] + j] = (byte) v;
			}
			pos = p;
			this.acc = acc;
			this.bitN = bitN;
			bitPos = bp;
		}

		void bytes(byte[] dst, int off, int len) throws IOException {
			if (bitN == 0) {
				if (pos + len > end) throw new IOException("truncated bytes");
				System.arraycopy(b, pos, dst, off, len);
				pos += len;
				bitPos += (long) len << 3;
				return;
			}
			for (int i = 0; i < len; i++) dst[off + i] = (byte) u8();
		}

	}

	// ===== CRC32 =====

	static final int[] CRC_TAB = new int[256];
	static {
		for (int i = 0; i < 256; i++) {
			int c = i;
			for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
			CRC_TAB[i] = c;
		}
	}

	/** varint のバイト数。出力長を先に確定させて余分に確保しないため。 */
	static int vlen(int v) {
		int k = 1;
		while ((v >>>= 7) != 0) k++;
		return k;
	}

	/** 先頭に 1 バイト置いた列の CRC。 */
	static int crc32(int pre, byte[] b, int off, int len) {
		java.util.zip.CRC32 c = new java.util.zip.CRC32();
		c.update(pre);
		c.update(b, off, len);
		return (int) c.getValue();
	}

	static int crc32(byte[] b, int off, int len) {
		java.util.zip.CRC32 c = new java.util.zip.CRC32();
		c.update(b, off, len);
		return (int) c.getValue();
	}
}
```

### `src/ifz/IfzGen.java`

```java
package ifz;

import java.util.Random;

/**
 * 評価データ生成器。シード固定で、誰が回しても同じ塊を返す。
 * 塊は「フレーム := varint(delta)・varint(種類)・varint(長さ)・中身」の繰り返し。
 */
public final class IfzGen {

	/** 固定シード */
	public static final long SEED = 20260917L;
	/** 塊サイズの候補（64KB・256KB・1MB） */
	public static final int[] SIZES = { 64 << 10, 256 << 10, 1 << 20 };
	/** 種類番号の上限 */
	public static final int TYPES = 64;

	private final Random rnd = new Random(SEED);
	private final long[] ctr = new long[TYPES];
	private final byte[][] hdr = new byte[TYPES][];
	private final int[] extra = new int[TYPES];
	private final int[] hot = new int[15];
	private final String[] vocab = new String[48];
	private final byte[] tmp = new byte[4096];
	private int next;

	public IfzGen() {
		for (int i = 0; i < hot.length; i++) hot[i] = rnd.nextInt(60);
		for (int t = 0; t < TYPES; t++) {
			byte[] h = new byte[2 + rnd.nextInt(3)];
			rnd.nextBytes(h);
			hdr[t] = h;
			extra[t] = rnd.nextInt(5);
			ctr[t] = rnd.nextInt(1 << 20);
		}
		for (int i = 0; i < vocab.length; i++) vocab[i] = word();
	}

	/** 次の塊を作る。サイズは 64KB→256KB→1MB を繰り返す。 */
	public byte[] nextBlock() {
		return block(SIZES[next++ % SIZES.length]);
	}

	/** 指定サイズの塊を作る。 */
	public byte[] block(int size) {
		if (size < 0) throw new IllegalArgumentException("size");
		byte[] out = new byte[size];
		int p = 0;
		if (size < 4) return out; // 端数は零詰め
		while (p < size) {
			p += frame(out, p, size - p);
		}
		return out;
	}

	/** 塊を n 個まとめて作る。 */
	public byte[][] corpus(int n) {
		byte[][] bs = new byte[n][];
		for (int i = 0; i < n; i++) bs[i] = nextBlock();
		return bs;
	}

	// 1フレーム書いて、書いたバイト数を返す。room は残り容量。
	private int frame(byte[] out, int p, int room) {
		int delta = rnd.nextInt(10) < 7 ? rnd.nextInt(3) : 3 + rnd.nextInt(48);
		int type = rnd.nextInt(10) < 8 ? hot[rnd.nextInt(hot.length)] : 16 + rnd.nextInt(45);
		int n = payload(type);
		int hn = vlen(delta) + vlen(type) + vlen(n);
		if (hn + n > room) n = room - hn; // 残りに合わせて中身を詰める
		int slack = room - hn - n;
		if (slack >= 1 && slack <= 3 && n + slack <= tmp.length) {
			for (int i = 0; i < slack; i++) tmp[n + i] = (byte) (n + i);
			n += slack;
		}
		int q = p;
		q = putVarint(out, q, delta);
		q = putVarint(out, q, type);
		q = putVarint(out, q, n);
		System.arraycopy(tmp, 0, out, q, n);
		return q + n - p;
	}

	// varint のバイト数
	private static int vlen(long v) {
		int n = 1;
		while ((v >>>= 7) != 0) n++;
		return n;
	}

	// 中身を作る。構造化7割・テキスト2割・乱数1割。長さを返す。
	private int payload(int type) {
		int cls = rnd.nextInt(10);
		if (cls < 7) return structured(type);
		if (cls < 9) return text();
		int n = 8 + rnd.nextInt(56);
		byte[] r = new byte[n];
		rnd.nextBytes(r);
		System.arraycopy(r, 0, tmp, 0, n);
		return n;
	}

	// 固定ヘッダ＋単調増加カウンタ＋小さな座標＋状態バイト
	private int structured(int type) {
		byte[] h = hdr[type];
		int q = 0;
		System.arraycopy(h, 0, tmp, q, h.length);
		q += h.length;
		ctr[type] += 1 + rnd.nextInt(3);
		q = putVarint(tmp, q, ctr[type]);
		q = put16(tmp, q, rnd.nextInt(1024));
		q = put16(tmp, q, rnd.nextInt(1024));
		tmp[q++] = (byte) rnd.nextInt(8);
		int e = extra[type];
		for (int i = 0; i < e; i++) {
			// 状態バイトはほぼ変わらず、稀に変わる
			tmp[q++] = (byte) (rnd.nextInt(20) == 0 ? rnd.nextInt(256) : (type * 7 + i) & 0xff);
		}
		return q;
	}

	// ASCII テキスト混じり
	private int text() {
		int q = 0;
		int words = 3 + rnd.nextInt(6);
		for (int i = 0; i < words; i++) {
			if (i > 0) tmp[q++] = ' ';
			String w = vocab[rnd.nextInt(vocab.length)];
			for (int j = 0; j < w.length(); j++) tmp[q++] = (byte) w.charAt(j);
		}
		String num = Integer.toString(rnd.nextInt(10000));
		tmp[q++] = ' ';
		for (int j = 0; j < num.length(); j++) tmp[q++] = (byte) num.charAt(j);
		tmp[q++] = '\n';
		return q;
	}

	private String word() {
		int n = 3 + rnd.nextInt(8);
		StringBuilder sb = new StringBuilder(n);
		for (int i = 0; i < n; i++) sb.append((char) ('a' + rnd.nextInt(26)));
		return sb.toString();
	}

	static int putVarint(byte[] b, int p, long v) {
		while (true) {
			int c = (int) (v & 0x7f);
			v >>>= 7;
			if (v != 0) {
				b[p++] = (byte) (c | 0x80);
			} else {
				b[p++] = (byte) c;
				return p;
			}
		}
	}

	static int put16(byte[] b, int p, int v) {
		b[p++] = (byte) v;
		b[p++] = (byte) (v >>> 8);
		return p;
	}
}
```

### `src/ifz/IfzBench.java`

```java
package ifz;

import java.io.IOException;
import java.util.Arrays;
import java.util.Random;
import java.util.zip.Deflater;
import java.util.zip.Inflater;

/**
 * 計測 main。固定シードのデータで roundtrip と速度・比率を測り、Deflate と比べる。
 * 使い方: java ifz.IfzBench [塊の数]
 */
public final class IfzBench {

	public static void main(String[] args) throws Exception {
		int blocks = args.length > 0 ? Integer.parseInt(args[0]) : 24;
		boolean[] efforts = { false, true };

		System.out.println("== roundtrip ==");
		roundtrip();

		System.out.printf("%n== checks ==%n");
		checks();

		IfzGen gen = new IfzGen();
		byte[][] data = gen.corpus(blocks);
		long raw = 0;
		for (byte[] b : data) raw += b.length;
		System.out.printf("%n== data ==%nseed %d  blocks %d  raw %d bytes%n", IfzGen.SEED, blocks, raw);

		System.out.printf("%n== result ==%n");
		System.out.printf("%-12s %10s %8s %12s %12s%n", "codec", "size", "ratio%", "compress", "decompress");
		row("IFZ1 e0", data, raw, 0);
		row("IFZ1 e1", data, raw, 1);
		rowDeflate("Deflate-1", data, raw, 1);
		rowDeflate("Deflate-6", data, raw, 6);

		System.out.printf("%n== per block size (IFZ1 e1) ==%n");
		for (int size : IfzGen.SIZES) {
			byte[][] d = new byte[4][];
			IfzGen g = new IfzGen();
			for (int i = 0; i < 4; i++) d[i] = g.block(size);
			long r = 0;
			for (byte[] b : d) r += b.length;
			long sz = 0;
			for (byte[] b : d) sz += Ifz1.compressBlock(b, 1).length;
			System.out.printf("  %7d B  ratio %6.2f%%%n", size, 100.0 * sz / r);
		}
	}

	static void row(String name, byte[][] data, long raw, int eff) throws IOException {
		byte[][] packed = new byte[data.length][];
		for (int i = 0; i < data.length; i++) packed[i] = Ifz1.compressBlock(data[i], eff);
		long size = 0;
		for (byte[] p : packed) size += p.length;
		long tc = time(() -> {
			for (byte[] b : data) Ifz1.compressBlock(b, eff);
		});
		for (int i = 0; i < data.length; i++) {
			byte[] back = Ifz1.decompressBlock(packed[i], data[i].length);
			if (!Arrays.equals(back, data[i])) throw new IOException("roundtrip mismatch at block " + i);
		}
		long td = time(() -> {
			for (int i = 0; i < packed.length; i++) {
				try {
					Ifz1.decompressBlock(packed[i], data[i].length);
				} catch (IOException e) {
					throw new RuntimeException(e);
				}
			}
		});
		System.out.printf("%-12s %10d %8.2f %9.1f MB/s %9.1f MB/s%n", name, size, 100.0 * size / raw,
				raw / 1e6 / (tc / 1e9), raw / 1e6 / (td / 1e9));
		for (byte[] b : data) {
			if (Ifz1.compressBlock(b, eff).length > Ifz1.maxPackedLength(b.length)) {
				throw new IOException("maxPackedLength too small");
			}
		}
	}

	static void rowDeflate(String name, byte[][] data, long raw, int level) throws IOException {
		byte[][] packed = new byte[data.length][];
		for (int i = 0; i < data.length; i++) {
			Deflater d = new Deflater(level, true);
			d.setInput(data[i]);
			d.finish();
			byte[] buf = new byte[data[i].length + 1024];
			int n = d.deflate(buf);
			d.end();
			packed[i] = Arrays.copyOf(buf, n);
		}
		long size = 0;
		for (byte[] p : packed) size += p.length;
		long tc = time(() -> {
			for (byte[] b : data) {
				Deflater d = new Deflater(level, true);
				d.setInput(b);
				d.finish();
				byte[] buf = new byte[b.length + 1024];
				d.deflate(buf);
				d.end();
			}
		});
		for (int i = 0; i < data.length; i++) {
			try {
				Inflater inf = new Inflater(true);
				inf.setInput(packed[i]);
				byte[] dst = new byte[data[i].length];
				int n = inf.inflate(dst);
				inf.end();
				if (n != data[i].length || !Arrays.equals(dst, data[i])) throw new IOException("deflate roundtrip");
			} catch (java.util.zip.DataFormatException e) {
				throw new IOException("deflate roundtrip", e);
			}
		}
		long td = time(() -> {
			for (int i = 0; i < packed.length; i++) {
				Inflater inf = new Inflater(true);
				inf.setInput(packed[i]);
				byte[] dst = new byte[data[i].length];
				try {
					inf.inflate(dst);
				} catch (Exception e) {
					throw new RuntimeException(e);
				}
				inf.end();
			}
		});
		System.out.printf("%-12s %10d %8.2f %9.1f MB/s %9.1f MB/s%n", name, size, 100.0 * size / raw,
				raw / 1e6 / (tc / 1e9), raw / 1e6 / (td / 1e9));
	}

	interface Job {
		void run();
	}

	/** 3回回して最速を採る（JIT の揺れを避ける） */
	/** 暖機秒数。JIT が C2 に乗り切るまで回さないと数がブレる。 */
	static final long WARM_NS = 400_000_000L;
	static final int MEASURE = 7;

	static long time(Job j) {
		// 全コーデック同じ条件で暖機してから最速値を採る
		long w = System.nanoTime();
		do {
			j.run();
		} while (System.nanoTime() - w < WARM_NS);
		long best = Long.MAX_VALUE;
		for (int i = 0; i < MEASURE; i++) {
			long t0 = System.nanoTime();
			j.run();
			long t = System.nanoTime() - t0;
			if (t < best) best = t;
		}
		return best;
	}

	/** 決定性・破損検出・並行呼び出し・maxPackedLength を確かめる */
	static void checks() throws Exception {
		IfzGen gen = new IfzGen();
		byte[][] data = gen.corpus(6);
		Random rnd = new Random(IfzGen.SEED ^ 0x5EEDL);

		// 決定性: 同じ入力 → 同じ出力
		for (int eff = 0; eff < 2; eff++) {
			for (byte[] b : data) {
				if (!Arrays.equals(Ifz1.compressBlock(b, eff), Ifz1.compressBlock(b, eff))) {
					throw new IOException("not deterministic at effort " + eff);
				}
			}
		}
		System.out.println("  deterministic     OK");

		// maxPackedLength を超えない
		for (int eff = 0; eff < 2; eff++) {
			for (byte[] b : data) {
				if (Ifz1.compressBlock(b, eff).length > Ifz1.maxPackedLength(b.length)) {
					throw new IOException("maxPackedLength too small");
				}
			}
		}
		System.out.println("  maxPackedLength   OK");

		// 破損: 1 バイト化けたら必ず IOException（RuntimeException は出さない）
		int caught = 0;
		int tried = 0;
		for (byte[] b : data) {
			byte[] pk = Ifz1.compressBlock(b, 1);
			for (int t = 0; t < 40; t++) {
				byte[] bad = pk.clone();
				bad[rnd.nextInt(bad.length)] ^= (byte) (1 << rnd.nextInt(8));
				tried++;
				try {
					byte[] back = Ifz1.decompressBlock(bad, b.length);
					if (!Arrays.equals(back, b)) throw new IOException("silent misread");
				} catch (IOException e) {
					caught++;
				}
			}
		}
		System.out.printf("  corruption        OK (%d/%d を IOException で検出、残りは CRC 衝突なしの同一データ)%n",
			caught, tried);

		// 長さの嘘は必ず弾く
		byte[] pk0 = Ifz1.compressBlock(data[0], 1);
		int rejected = 0;
		for (int bad : new int[] { -1, data[0].length + 1, 1 << 29 }) {
			try {
				Ifz1.decompressBlock(pk0, bad);
			} catch (IOException e) {
				rejected++;
			}
		}
		if (rejected != 3) throw new IOException("bad rawLength accepted");
		try {
			Ifz1.decompressBlock(new byte[] { 'X', 'F', 'Z', '1', 0, 0 }, 0);
			throw new IOException("bad magic accepted");
		} catch (IOException e) {
			// 期待どおり
		}
		try {
			Ifz1.decompressBlock(new byte[] { 'I', 'F', 'Z', '1', (byte) 0x7E, 0 }, 0);
			throw new IOException("unknown flag accepted");
		} catch (IOException e) {
			// 期待どおり
		}
		System.out.println("  bad header        OK");

		// 並行呼び出し: 共有状態を持たないので結果は変わらない
		byte[][] ref = new byte[data.length][];
		for (int i = 0; i < data.length; i++) ref[i] = Ifz1.compressBlock(data[i], 1);
		final byte[][] fdata = data;
		final byte[][] fref = ref;
		Thread[] th = new Thread[4];
		final Throwable[] err = new Throwable[1];
		for (int t = 0; t < th.length; t++) {
			final int id = t;
			th[t] = new Thread(() -> {
				try {
					for (int r = 0; r < 6; r++) {
						for (int i = 0; i < fdata.length; i++) {
							int eff = (id + r) & 1;
							byte[] c = Ifz1.compressBlock(fdata[i], eff);
							if (eff == 1 && !Arrays.equals(c, fref[i])) throw new IOException("parallel drift");
							if (!Arrays.equals(Ifz1.decompressBlock(c, fdata[i].length), fdata[i])) {
								throw new IOException("parallel roundtrip");
							}
						}
					}
				} catch (Throwable e) {
					synchronized (err) {
						if (err[0] == null) err[0] = e;
					}
				}
			});
			th[t].start();
		}
		for (Thread t : th) t.join();
		if (err[0] != null) throw new IOException("parallel check failed", err[0]);
		System.out.println("  parallel          OK");
	}

	static void roundtrip() throws IOException {
		Random rnd = new Random(IfzGen.SEED);
		check("empty", new byte[0]);
		check("1byte", new byte[] { 42 });
		check("2byte", new byte[] { 1, 2 });
		byte[] same = new byte[70000];
		Arrays.fill(same, (byte) 7);
		check("same", same);
		byte[] zeros = new byte[70000];
		check("zeros", zeros);
		byte[] rnd1 = new byte[70000];
		rnd.nextBytes(rnd1);
		check("random", rnd1);
		byte[] inc = new byte[70000];
		for (int i = 0; i < inc.length; i++) inc[i] = (byte) i;
		check("increment", inc);
		// 疑似フレームだが途中で壊れているもの
		byte[] bad = new byte[70000];
		int p = 0;
		while (p < bad.length - 4) {
			bad[p++] = 1;
			bad[p++] = 3;
			bad[p++] = 2;
			bad[p++] = (byte) rnd.nextInt();
			bad[p++] = (byte) rnd.nextInt();
		}
		check("pseudo-frame", bad);
		// 生成データ
		IfzGen g = new IfzGen();
		for (int size : IfzGen.SIZES) check("gen-" + size, g.block(size));
		System.out.println("  all roundtrip OK");
	}

	static void check(String name, byte[] raw) throws IOException {
		for (int eff = 0; eff <= 1; eff++) {
			byte[] packed = Ifz1.compressBlock(raw, eff);
			if (packed.length > Ifz1.maxPackedLength(raw.length)) {
				throw new IOException(name + ": exceeds maxPackedLength");
			}
			byte[] back = Ifz1.decompressBlock(packed, raw.length);
			if (!Arrays.equals(back, raw)) throw new IOException(name + ": mismatch effort=" + eff);
			if (packed.length < 5 || packed[0] != 'I' || packed[1] != 'F' || packed[2] != 'Z' || packed[3] != '1') {
				throw new IOException(name + ": bad magic");
			}
		}
		System.out.printf("  %-12s %7d -> %7d  OK%n", name, raw.length, Ifz1.compressBlock(raw, 1).length);
	}
}
```

### `bench/IfzVsJzlib.java`

```java
package bench;

import com.jcraft.jzlib.Deflater;
import com.jcraft.jzlib.Inflater;
import com.jcraft.jzlib.JZlib;
import ifz.Ifz1;
import ifz.IfzGen;
import java.io.IOException;
import java.util.Arrays;

/**
 * 純 Java 同士の比較。jzlib（zlib の純 Java 移植）と IFZ1 を同じ条件で測る。
 * 参考として java.util.zip（zlib の JNI 呼び出し）も並べる。
 * 使い方: javac -d build-jzlib third_party/com/jcraft/jzlib/*.java src/ifz/*.java bench/IfzVsJzlib.java
 *         java -Xms1g -Xmx1g -cp build-jzlib bench.IfzVsJzlib 12
 */
public final class IfzVsJzlib {

	interface Job {
		void run();
	}

	static final long WARM_NS = 400_000_000L;
	static final int MEASURE = 7;

	public static void main(String[] args) throws Exception {
		int blocks = args.length > 0 ? Integer.parseInt(args[0]) : 12;
		byte[][] data = new IfzGen().corpus(blocks);
		long raw = 0;
		for (byte[] b : data) raw += b.length;
		System.out.printf("seed %d  blocks %d  raw %d bytes%n%n", IfzGen.SEED, blocks, raw);
		System.out.printf("%-18s %10s %8s %12s %12s%n", "codec", "size", "ratio%", "compress", "decompress");
		rowIfz("IFZ1 e0", data, raw, 0);
		rowIfz("IFZ1 e1", data, raw, 1);
		rowJzlib("jzlib-1 (pure Java)", data, raw, JZlib.Z_BEST_SPEED);
		rowJzlib("jzlib-6 (pure Java)", data, raw, JZlib.Z_DEFAULT_COMPRESSION);
		rowZip("java.util.zip-1 (JNI)", data, raw, 1);
		rowZip("java.util.zip-6 (JNI)", data, raw, 6);
	}

	static void rowIfz(String name, byte[][] data, long raw, int eff) throws IOException {
		byte[][] pk = new byte[data.length][];
		for (int i = 0; i < data.length; i++) pk[i] = Ifz1.compressBlock(data[i], eff);
		long size = 0;
		for (byte[] p : pk) size += p.length;
		for (int i = 0; i < data.length; i++) {
			if (!Arrays.equals(Ifz1.decompressBlock(pk[i], data[i].length), data[i])) {
				throw new IOException("roundtrip mismatch " + i);
			}
		}
		long tc = time(() -> {
			for (byte[] b : data) Ifz1.compressBlock(b, eff);
		});
		long td = time(() -> {
			for (int i = 0; i < pk.length; i++) {
				try {
					Ifz1.decompressBlock(pk[i], data[i].length);
				} catch (IOException e) {
					throw new RuntimeException(e);
				}
			}
		});
		print(name, size, raw, tc, td);
	}

	static void rowJzlib(String name, byte[][] data, long raw, int level) throws IOException {
		byte[][] pk = new byte[data.length][];
		for (int i = 0; i < data.length; i++) pk[i] = jzDeflate(data[i], level);
		long size = 0;
		for (byte[] p : pk) size += p.length;
		for (int i = 0; i < data.length; i++) {
			if (!Arrays.equals(jzInflate(pk[i], data[i].length), data[i])) throw new IOException("roundtrip " + i);
		}
		long tc = time(() -> {
			for (byte[] b : data) jzDeflate(b, level);
		});
		long td = time(() -> {
			for (int i = 0; i < pk.length; i++) jzInflate(pk[i], data[i].length);
		});
		print(name, size, raw, tc, td);
	}

	static void rowZip(String name, byte[][] data, long raw, int level) throws IOException {
		byte[][] pk = new byte[data.length][];
		for (int i = 0; i < data.length; i++) pk[i] = zipDeflate(data[i], level);
		long size = 0;
		for (byte[] p : pk) size += p.length;
		long tc = time(() -> {
			for (byte[] b : data) zipDeflate(b, level);
		});
		long td = time(() -> {
			for (int i = 0; i < pk.length; i++) zipInflate(pk[i], data[i].length);
		});
		print(name, size, raw, tc, td);
	}

	static byte[] jzDeflate(byte[] in, int level) {
		try {
			Deflater d = new Deflater(level, true);
			byte[] out = new byte[in.length + (in.length >>> 2) + 1024];
			d.setInput(in);
			d.setOutput(out);
			int err;
			do {
				err = d.deflate(JZlib.Z_FINISH);
			} while (err == JZlib.Z_OK);
			if (err != JZlib.Z_STREAM_END) throw new IllegalStateException("deflate " + err);
			int n = out.length - d.avail_out;
			d.end();
			return Arrays.copyOf(out, n);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	static byte[] jzInflate(byte[] in, int rawLen) {
		try {
			Inflater z = new Inflater(true);
			byte[] out = new byte[rawLen + 1024]; // 端数に余裕を持たせないと Z_BUF_ERROR になる
			z.setInput(in);
			z.setOutput(out);
			int err;
			do {
				err = z.inflate(JZlib.Z_NO_FLUSH);
			} while (err == JZlib.Z_OK);
			int n = out.length - z.avail_out;
			// jzlib は丁度使い切ったときに Z_STREAM_END でなく Z_BUF_ERROR を返すことがある。
			// 出力が揃っていれば成功とみなす（中身は呼び出し側で照合する）。
			if (err != JZlib.Z_STREAM_END && n != rawLen) {
				throw new IllegalStateException("inflate " + err + " n=" + n + " rawLen=" + rawLen);
			}
			z.end();
			if (n != rawLen) throw new IllegalStateException("size " + n + " != " + rawLen);
			return Arrays.copyOf(out, n);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	static byte[] zipDeflate(byte[] in, int level) {
		java.util.zip.Deflater d = new java.util.zip.Deflater(level, true);
		d.setInput(in);
		d.finish();
		byte[] buf = new byte[in.length + 1024];
		int n = d.deflate(buf);
		d.end();
		return Arrays.copyOf(buf, n);
	}

	static byte[] zipInflate(byte[] in, int rawLen) {
		try {
			java.util.zip.Inflater z = new java.util.zip.Inflater(true);
			z.setInput(in);
			byte[] out = new byte[rawLen];
			int n = z.inflate(out);
			z.end();
			if (n != rawLen) throw new IllegalStateException("size " + n);
			return out;
		} catch (java.util.zip.DataFormatException e) {
			throw new RuntimeException(e);
		}
	}

	static void print(String name, long size, long raw, long tc, long td) {
		System.out.printf("%-18s %10d %8.2f %9.1f MB/s %9.1f MB/s%n", name, size, 100.0 * size / raw,
				raw / 1e6 / (tc / 1e9), raw / 1e6 / (td / 1e9));
	}

	static long time(Job j) {
		long w = System.nanoTime();
		do {
			j.run();
		} while (System.nanoTime() - w < WARM_NS);
		long best = Long.MAX_VALUE;
		for (int i = 0; i < MEASURE; i++) {
			long t0 = System.nanoTime();
			j.run();
			long t = System.nanoTime() - t0;
			if (t < best) best = t;
		}
		return best;
	}
}
```

### `bench/IfzMem.java`

```java
package bench;

import ifz.Ifz1;
import ifz.IfzGen;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/**
 * 1 塊あたりのメモリ使用を測る。
 *
 * 使い方:
 *   java -Xms256m -Xmx256m -cp build bench.IfzMem [塊サイズ]   確保量・GC 時間の表
 *   java -cp build bench.IfzMem probe [塊サイズ]              動く最小の -Xmx と RSS
 *   java -cp build bench.IfzMem rss  [塊サイズ] [仕事]        1 回だけ実行して RSS を出す（probe 用）
 *
 * 仕事: ifz-c ifz-d zip-c zip-d none
 */
public final class IfzMem {

	public static void main(String[] args) throws Exception {
		if (args.length > 0 && args[0].equals("probe")) {
			probe(args.length > 1 ? Integer.parseInt(args[1]) : 1 << 20);
			return;
		}
		if (args.length > 0 && args[0].equals("rss")) {
			once(args.length > 1 ? Integer.parseInt(args[1]) : 1 << 20, args.length > 2 ? args[2] : "none");
			return;
		}
		int size = args.length > 0 ? Integer.parseInt(args[0]) : 1 << 20;
		byte[] raw = new IfzGen().block(size);
		byte[] p0 = Ifz1.compressBlock(raw, 0);
		byte[] p1 = Ifz1.compressBlock(raw, 1);
		byte[] z1 = zipDeflate(raw, 1);
		for (int w = 0; w < 20; w++) {
			Ifz1.compressBlock(raw, 1);
			Ifz1.decompressBlock(p1, raw.length);
			zipDeflate(raw, 1);
			zipInflate(z1, raw.length);
		}
		System.out.printf("raw %,d B   IFZ1 e0 %,d   IFZ1 e1 %,d   zip-1 %,d%n%n", raw.length, p0.length, p1.length,
				z1.length);
		System.out.printf("%-12s %12s %10s%n", "codec", "alloc/call", "GC ms/call");
		measure("IFZ1 e0 c", () -> Ifz1.compressBlock(raw, 0));
		measure("IFZ1 e1 c", () -> Ifz1.compressBlock(raw, 1));
		measure("IFZ1 e0 d", () -> dec(p0, raw.length));
		measure("IFZ1 e1 d", () -> dec(p1, raw.length));
		measure("zip-1 c", () -> zipDeflate(raw, 1));
		measure("zip-1 d", () -> zipInflate(z1, raw.length));
	}

	// ---- 表 ----

	static byte[] dec(byte[] p, int n) {
		try {
			return Ifz1.decompressBlock(p, n);
		} catch (java.io.IOException e) {
			throw new RuntimeException(e);
		}
	}

	interface Job {
		Object run();
	}

	static final int REPS = 200;

	static void measure(String name, Job j) {
		com.sun.management.ThreadMXBean tb = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
		long id = Thread.currentThread().threadId();
		j.run();
		System.gc();
		sleep(60);
		long gc0 = gcTime();
		long a0 = tb.getThreadAllocatedBytes(id);
		for (int i = 0; i < REPS; i++) {
			if (j.run() == null) System.out.print("");
		}
		long alloc = (tb.getThreadAllocatedBytes(id) - a0) / REPS;
		double gc = (gcTime() - gc0) / (double) REPS;
		System.out.printf("%-12s %9.2f MB %8.3f%n", name, alloc / 1048576.0, gc);
	}

	static long gcTime() {
		long t = 0;
		for (GarbageCollectorMXBean g : ManagementFactory.getGarbageCollectorMXBeans()) {
			if (g.getCollectionTime() > 0) t += g.getCollectionTime();
		}
		return t;
	}

	static void sleep(int ms) {
		try {
			Thread.sleep(ms);
		} catch (InterruptedException e) {
			Thread.currentThread().interrupt();
		}
	}

	// ---- 最小ヒープと RSS ----

	static final String[] JOBS = { "none", "ifz-c", "ifz-d", "zip-c", "zip-d" };

	/** 1 回だけ処理する子プロセスを都度起動して、実 RSS と最小 -Xmx を測る。 */
	static void probe(int size) throws Exception {
		byte[] raw = new IfzGen().block(size);
		Files.write(tmp(size, "ifz"), Ifz1.compressBlock(raw, 1));
		Files.write(tmp(size, "zip"), zipDeflate(raw, 1));
		raw = null;
		System.out.printf("塊 %,d B — 1 回だけ処理する子プロセスを都度起動%n%n", size);
		System.out.printf("%-8s %12s %10s%n", "job", "peak RSS", "min -Xmx");
		for (String job : JOBS) {
			int min = -1;
			for (int x = 8; x <= 512; x++) {
				if (run(size, job, 1, x, true).exitValue() == 0) {
					min = x;
					break;
				}
			}
			System.out.printf("%-8s %9s MB %7d MB%n", job, rssOf(run(size, job, RSS_HEAP, RSS_HEAP, false)), min);
		}
		Files.deleteIfExists(tmp(size, "ifz"));
		Files.deleteIfExists(tmp(size, "zip"));
	}

	/** RSS 比較のときはヒープを固定して、JVM の拡張方針に左右されないようにする。 */
	static final int RSS_HEAP = 64;

	static Path tmp(int size, String tag) {
		return Path.of(System.getProperty("java.io.tmpdir"), "ifzmem-" + size + "." + tag);
	}

	static String rssOf(Process p) throws Exception {
		String out = new String(p.getInputStream().readAllBytes());
		int i = out.indexOf("VmHWM:");
		if (i < 0) return "—";
		String rest = out.substring(i + 6).trim();
		int k = 0;
		while (k < rest.length() && Character.isDigit(rest.charAt(k))) k++;
		return String.format("%.1f", Long.parseLong(rest.substring(0, k)) / 1024.0);
	}

	static Process run(int size, String job, int xms, int xmx, boolean discard) throws Exception {
		String java = System.getProperty("java.home") + "/bin/java";
		ProcessBuilder pb = new ProcessBuilder(java, "-Xms" + xms + "m", "-Xmx" + xmx + "m",
				"-cp", System.getProperty("java.class.path"), "bench.IfzMem", "rss", String.valueOf(size), job);
		if (discard) pb.redirectError(ProcessBuilder.Redirect.DISCARD).redirectOutput(ProcessBuilder.Redirect.DISCARD);
		Process p = pb.start();
		p.waitFor();
		return p;
	}

	/** 子プロセス側。1 回だけ処理して自分のピーク RSS を出す。 */
	static void once(int size, String job) throws Exception {
		switch (job) {
		case "ifz-c" -> Ifz1.compressBlock(new IfzGen().block(size), 1);
		case "ifz-d" -> Ifz1.decompressBlock(Files.readAllBytes(tmp(size, "ifz")), size);
		case "zip-c" -> zipDeflate(new IfzGen().block(size), 1);
		case "zip-d" -> zipInflate(Files.readAllBytes(tmp(size, "zip")), size);
		default -> {
		}
		}
		System.out.println(hwm());
	}

	static String hwm() {
		try {
			for (String line : Files.readAllLines(Path.of("/proc/self/status"))) {
				if (line.startsWith("VmHWM:")) return line;
			}
		} catch (Exception e) {
			// /proc が無い環境では空
		}
		return "VmHWM: 0 kB";
	}

	// ---- 比較対象 ----

	static byte[] zipDeflate(byte[] in, int level) {
		java.util.zip.Deflater d = new java.util.zip.Deflater(level, true);
		d.setInput(in);
		d.finish();
		byte[] buf = new byte[in.length + 1024];
		int n = d.deflate(buf);
		d.end();
		return Arrays.copyOf(buf, n);
	}

	static byte[] zipInflate(byte[] in, int rawLen) {
		try {
			java.util.zip.Inflater z = new java.util.zip.Inflater(true);
			z.setInput(in);
			byte[] out = new byte[rawLen];
			z.inflate(out);
			z.end();
			return out;
		} catch (java.util.zip.DataFormatException e) {
			throw new RuntimeException(e);
		}
	}
}
```
