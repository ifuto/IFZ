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
