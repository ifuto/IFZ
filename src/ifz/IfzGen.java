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
