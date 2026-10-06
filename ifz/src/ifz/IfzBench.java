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
