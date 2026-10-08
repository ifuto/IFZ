import org.bukkit.configuration.file.YamlConfiguration;

import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Proves how the plugin's message loader behaves, using the REAL Bukkit implementation.
 *
 * LocaleService does: YamlConfiguration.getKeys(true) to build a catalog, then getString(path)
 * to read a message back. This probe runs that exact pair against a locale file and reports the
 * keys the loader can never resolve.
 *
 * Usage: java LocalePathProbe <lang-dir> [keys...]
 */
public final class LocalePathProbe {

    public static void main(String[] args) throws Exception {
        Path langDir = Path.of(args[0]);
        List<String> probes = new ArrayList<>();
        for (int i = 1; i < args.length; i++) {
            probes.add(args[i]);
        }
        if (probes.isEmpty()) {
            probes.add("gui.party-launch-title");
            probes.add("gui.battle-mode-ffa");
            probes.add("duel-gui.kb-title");
            probes.add("queue.same-ip-notice");
            probes.add("party.selected");
            probes.add("menu.yes");
            probes.add("menu.page-next");
        }

        for (File file : sortedYml(langDir)) {
            YamlConfiguration yaml;
            try (Reader reader = new InputStreamReader(Files.newInputStream(file.toPath()),
                    StandardCharsets.UTF_8)) {
                yaml = YamlConfiguration.loadConfiguration(reader);
            }
            // Exactly what LocaleService#flattenInto does.
            Map<String, String> catalog = new ConcurrentHashMap<>();
            for (String key : yaml.getKeys(true)) {
                if (yaml.isString(key)) {
                    catalog.put(key, yaml.getString(key));
                }
            }

            int dead = 0;
            for (String key : yaml.getKeys(true)) {
                if (yaml.isConfigurationSection(key) || !yaml.isString(key)) {
                    continue;
                }
                // Was this path reachable as a REAL leaf, or only as a section name holder?
                if (!yaml.isString(key)) {
                    dead++;
                }
            }

            StringBuilder out = new StringBuilder(file.getName() + ": catalog=" + catalog.size());
            for (String probe : probes) {
                String value = catalog.get(probe);
                out.append("\n   ").append(probe).append(" -> ")
                        .append(value == null ? "!!! MISSING (renders as !" + probe + "!)"
                                : "\"" + trim(value) + "\"");
            }
            System.out.println(out);
        }
    }

    private static String trim(String value) {
        String flat = value.replace('\n', ' ');
        return flat.length() > 42 ? flat.substring(0, 42) + "..." : flat;
    }

    private static List<File> sortedYml(Path dir) throws Exception {
        List<File> files = new ArrayList<>();
        try (var stream = Files.list(dir)) {
            stream.filter(p -> p.toString().endsWith(".yml"))
                    .sorted()
                    .forEach(p -> files.add(p.toFile()));
        }
        return files;
    }
}
