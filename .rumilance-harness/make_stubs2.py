#!/usr/bin/env python3
"""Extend the compile-only stubs (Hikari, LuckPerms, the rest of the PacketEvents surface).

Run after make_stubs.py; it overwrites the stub files that needed more surface and adds the
missing families, then recompiles the whole stub tree.

Usage: python3 make_stubs2.py <out-dir>
"""
import pathlib
import subprocess
import sys

JDK = "/tmp/toolchain/x/jdk-21.0.12.1+1"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/toolchain/stubs")
SRC = OUT / "src"
CLS = OUT / "classes"

PACKET_TYPE_SERVER = [
    "ATTACH_ENTITY", "BLOCK_CHANGE", "BLOCK_ENTITY_DATA", "CHUNK_DATA", "DESTROY_ENTITIES",
    "ENTITY_ANIMATION", "ENTITY_EFFECT", "ENTITY_EQUIPMENT", "ENTITY_HEAD_LOOK",
    "ENTITY_METADATA", "ENTITY_MOVEMENT", "ENTITY_RELATIVE_MOVE",
    "ENTITY_RELATIVE_MOVE_AND_ROTATION", "ENTITY_ROTATION", "ENTITY_STATUS", "ENTITY_TELEPORT",
    "ENTITY_VELOCITY", "HURT_ANIMATION", "NAMED_SOUND_EFFECT", "OPEN_SIGN_EDITOR",
    "PLAYER_INFO_REMOVE", "PLAYER_INFO_UPDATE", "REMOVE_ENTITY_EFFECT", "SET_PASSENGERS",
    "SPAWN_ENTITY", "SPAWN_PLAYER", "SPAWN_EXPERIENCE_ORB", "SOUND_EFFECT", "UPDATE_ATTRIBUTES",
    "SYSTEM_CHAT_MESSAGE", "RESPAWN", "JOIN_GAME",
]

FILES = {}

FILES["com/github/retrooper/packetevents/event/PacketListener.java"] = f"""
package com.github.retrooper.packetevents.event;
/** Compile-only stub. */
public interface PacketListener {{
    default void onPacketSend(PacketSendEvent event) {{ }}
    default void onPacketReceive(PacketReceiveEvent event) {{ }}
    default void onUserConnect(Object user) {{ }}
}}
"""

FILES["com/github/retrooper/packetevents/protocol/packettype/PacketType.java"] = """
package com.github.retrooper.packetevents.protocol.packettype;
/** Compile-only stub. */
public final class PacketType {
""" + "".join(f"""
    private static PacketTypeCommon c() {{ return new PacketTypeCommon(); }}""" for _ in [0]) + """
    public static final class Play {
        public static final class Server {
""" + "".join(f"            public static final PacketTypeCommon {c} = new PacketTypeCommon();\n"
              for c in PACKET_TYPE_SERVER) + """        }
        public static final class Client {
            public static final PacketTypeCommon UPDATE_SIGN = new PacketTypeCommon();
            public static final PacketTypeCommon INTERACT_ENTITY = new PacketTypeCommon();
            public static final PacketTypeCommon PLAYER_INPUT = new PacketTypeCommon();
            public static final PacketTypeCommon PLAYER_ACTION = new PacketTypeCommon();
            public static final PacketTypeCommon KEEP_ALIVE = new PacketTypeCommon();
            public static final PacketTypeCommon CLIENT_SETTINGS = new PacketTypeCommon();
            public static final PacketTypeCommon INTERACT_ITEM = new PacketTypeCommon();
            public static final PacketTypeCommon HELD_ITEM_CHANGE = new PacketTypeCommon();
        }
    }
    public static final class Configuration {
        public static final class Server { }
        public static final class Client { }
    }
    public static final class Status {
        public static final class Server { }
        public static final class Client { }
    }
}
"""

FILES["com/github/retrooper/packetevents/protocol/world/Location.java"] = """
package com.github.retrooper.packetevents.protocol.world;
/** Compile-only stub. */
public class Location {
    public Location(double x, double y, double z) { }
    public Location(double x, double y, double z, float yaw, float pitch) { }
    public double getX() { return 0; }
    public double getY() { return 0; }
    public double getZ() { return 0; }
    public float getYaw() { return 0; }
    public float getPitch() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/protocol/player/User.java"] = """
package com.github.retrooper.packetevents.protocol.player;
/** Compile-only stub. */
public interface User {
    void sendPacket(Object packet);
    int getEntityId();
}
"""

FILES["com/github/retrooper/packetevents/protocol/player/PlayerManager.java"] = """
package com.github.retrooper.packetevents.protocol.player;
/** Compile-only stub. */
public final class PlayerManager {
    public void sendPacket(Object player, Object packet) { }
    public User getUser(Object player) { return null; }
}
"""

FILES["com/github/retrooper/packetevents/util/UserManager.java"] = """
package com.github.retrooper.packetevents.util;
import com.github.retrooper.packetevents.protocol.player.User;
/** Compile-only stub. */
public final class UserManager {
    public User getUser(java.util.UUID id) { return null; }
}
"""

FILES["io/github/retrooper/packetevents/util/SpigotConversionUtil.java"] = """
package io.github.retrooper.packetevents.util;
import com.github.retrooper.packetevents.protocol.world.Location;
/** Compile-only stub (the plugin also imports the older io.github package). */
public final class SpigotConversionUtil {
    private SpigotConversionUtil() { }
    public static Location fromBukkitLocation(org.bukkit.Location location) { return null; }
    public static org.bukkit.Location toBukkitLocation(Location location) { return null; }
    public static Object fromBukkitBlockData(org.bukkit.block.data.BlockData data) { return null; }
    public static Object fromBukkitItemStack(org.bukkit.inventory.ItemStack stack) { return null; }
    public static org.bukkit.inventory.ItemStack toBukkitItemStack(Object stack) { return null; }
    public static Object fromBukkitVector(org.bukkit.util.Vector vector) { return null; }
}
"""

# -- the wrappers that needed extra constructors / members -------------------
EXTRA_WRAPPERS = {
    "WrapperPlayServerEntityStatus": ["public WrapperPlayServerEntityStatus(int entityId, int status) { super(); }"],
    "WrapperPlayServerEntityMetadata": ["public WrapperPlayServerEntityMetadata(int entityId, java.util.List<com.github.retrooper.packetevents.protocol.entity.data.EntityData> data) { super(); }"],
    "WrapperPlayServerEntityHeadLook": ["public WrapperPlayServerEntityHeadLook(int entityId, float headYaw) { super(); }"],
    "WrapperPlayServerUpdateAttributes": ["public int getEntityId() { return 0; }"],
    "WrapperPlayServerPlayerInfoRemove": [
        "public WrapperPlayServerPlayerInfoRemove(java.util.UUID uuid) { super(); }",
        "public WrapperPlayServerPlayerInfoRemove(java.util.List<java.util.UUID> uuids) { super(); }",
    ],
    "WrapperPlayServerChunkData": ["public Object getColumn() { return null; }"],
    "WrapperPlayServerSpawnEntity": [
        "public WrapperPlayServerSpawnEntity(int entityId, java.util.UUID uuid, Object type, "
        "com.github.retrooper.packetevents.protocol.world.Location location) { super(); }",
    ],
}

for name, members in EXTRA_WRAPPERS.items():
    body = "\n".join("    " + m for m in members)
    # keep only one getEntityId(): the template already provides the plain accessor
    generic = "" if any("getEntityId" in m for m in members) else "    public int getEntityId() { return 0; }\n"
    FILES[f"com/github/retrooper/packetevents/wrapper/play/server/{name}.java"] = f"""
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class {name} extends PacketWrapper<{name}> {{
    public {name}(PacketSendEvent event) {{ super(event); }}
    public {name}(int entityId) {{ super(); }}
{generic}{body}
}}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerPlayerInfoUpdate.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.player.GameMode;
import com.github.retrooper.packetevents.protocol.player.UserProfile;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
import java.util.List;
/** Compile-only stub. */
public class WrapperPlayServerPlayerInfoUpdate extends PacketWrapper<WrapperPlayServerPlayerInfoUpdate> {

    public enum Action { ADD_PLAYER, INITIALIZE_CHAT, UPDATE_GAME_MODE, UPDATE_LISTED, UPDATE_LATENCY, UPDATE_DISPLAY_NAME }

    public static class PlayerInfo {
        public PlayerInfo(UserProfile profile, boolean listed, int latency, GameMode gameMode,
                          net.kyori.adventure.text.Component displayName, Object chatSession) { }
    }

    public WrapperPlayServerPlayerInfoUpdate(PacketSendEvent event) { super(event); }
    public WrapperPlayServerPlayerInfoUpdate(Action action, List<PlayerInfo> entries) { super(); }
    public WrapperPlayServerPlayerInfoUpdate(java.util.Set<Action> actions, List<PlayerInfo> entries) { super(); }
    public List<PlayerInfo> getEntries() { return List.of(); }
}
"""

# -- HikariCP (compile-only) -------------------------------------------------
FILES["com/zaxxer/hikari/HikariConfig.java"] = """
package com.zaxxer.hikari;
import java.util.Properties;
/** Compile-only stub. */
public class HikariConfig {
    public HikariConfig() { }
    public HikariConfig(Properties properties) { }
    public void setPoolName(String poolName) { }
    public void setDriverClassName(String driverClassName) { }
    public void setJdbcUrl(String jdbcUrl) { }
    public void setUsername(String username) { }
    public void setPassword(String password) { }
    public void setMaximumPoolSize(int size) { }
    public void setMinimumIdle(int idle) { }
    public void setConnectionTimeout(long millis) { }
    public void setIdleTimeout(long millis) { }
    public void setMaxLifetime(long millis) { }
    public void setLeakDetectionThreshold(long millis) { }
    public void setConnectionTestQuery(String query) { }
    public void addDataSourceProperty(String name, Object value) { }
    public Properties getDataSourceProperties() { return new Properties(); }
}
"""

FILES["com/zaxxer/hikari/HikariDataSource.java"] = """
package com.zaxxer.hikari;
import java.sql.Connection;
import java.sql.SQLException;
/** Compile-only stub. */
public class HikariDataSource extends HikariConfig implements AutoCloseable {
    public HikariDataSource(HikariConfig config) { }
    public Connection getConnection() throws SQLException { return null; }
    public Connection getConnection(long timeoutMs) throws SQLException { return null; }
    @Override public void close() { }
}
"""

# -- LuckPerms (compile-only) ------------------------------------------------
FILES["net/luckperms/api/LuckPerms.java"] = """
package net.luckperms.api;
import net.luckperms.api.model.user.UserManager;
/** Compile-only stub. */
public interface LuckPerms {
    UserManager getUserManager();
}
"""
FILES["net/luckperms/api/LuckPermsProvider.java"] = """
package net.luckperms.api;
/** Compile-only stub. */
public final class LuckPermsProvider {
    public static LuckPerms get() { return null; }
}
"""
FILES["net/luckperms/api/model/user/UserManager.java"] = """
package net.luckperms.api.model.user;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
/** Compile-only stub. */
public interface UserManager {
    User getUser(UUID uniqueId);
    User getUser(String username);
    CompletableFuture<User> loadUser(UUID uniqueId);
    CompletableFuture<Void> saveUser(User user);
}
"""
FILES["net/luckperms/api/model/user/User.java"] = """
package net.luckperms.api.model.user;
import net.luckperms.api.node.Node;
import net.luckperms.api.node.NodeType;
import java.util.Collection;
/** Compile-only stub. */
public interface User {
    UserData data();
    Collection<Node> getNodes(NodeType type);
    Collection<Node> getNodes();
}
"""
FILES["net/luckperms/api/model/user/UserData.java"] = """
package net.luckperms.api.model.user;
import net.luckperms.api.node.Node;
/** Compile-only stub. */
public interface UserData {
    boolean add(Node node);
    boolean remove(Node node);
}
"""
FILES["net/luckperms/api/node/Node.java"] = """
package net.luckperms.api.node;
/** Compile-only stub. */
public class Node {
    public static Builder builder(String key) { return null; }
    public String getKey() { return ""; }
    public boolean getValue() { return true; }
    public boolean isBlank() { return false; }
    public Node trim() { return this; }
    /** Compile-only stub. */
    public static class Builder {
        public Builder value(boolean value) { return this; }
        public Builder expire(java.time.Duration duration) { return this; }
        public Node build() { return null; }
    }
}
"""
FILES["net/luckperms/api/node/NodeType.java"] = """
package net.luckperms.api.node;
/** Compile-only stub. */
public final class NodeType<T extends Node> {
    public static final NodeType<Node> PERMISSION = new NodeType<>();
}
"""

for rel, body in FILES.items():
    target = SRC / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.lstrip(), encoding="utf-8")

CLS.mkdir(parents=True, exist_ok=True)
# The stubs reference Bukkit types (SpigotConversionUtil), so the delivered server has to be on
# the stub classpath as well.
cp = [str(p) for p in sorted(pathlib.Path("/tmp/toolchain/paper-run/libraries").rglob("*.jar"))]
cp.append("/tmp/toolchain/paper-run/versions/1.21.11/paper-1.21.11.jar")
classpath = ":".join(cp)
sources = [str(p) for p in sorted(SRC.rglob("*.java"))]
for attempt in range(1, 4):
    result = subprocess.run([f"{JDK}/bin/javac", "-nowarn", "-cp", classpath, "-d", str(CLS), *sources],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"stubs compiled: {len(sources)} sources -> {len(list(CLS.rglob('*.class')))} classes")
        break
    print(f"attempt {attempt} failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}", file=sys.stderr)
else:
    raise SystemExit(1)
