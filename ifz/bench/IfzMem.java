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
