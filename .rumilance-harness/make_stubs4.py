#!/usr/bin/env python3
"""Last stub layer: real-shaped PacketType classes, remaining wrappers, WorldEdit surface.

Run after make_stubs.py / make_stubs2.py / make_stubs3.py, then the plugin tree compiles
clean with javac against the delivered Paper jar. Usage: python3 make_stubs4.py <out-dir>
"""
import pathlib
import subprocess
import sys

JDK = "/tmp/toolchain/x/jdk-21.0.12.1+1"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/toolchain/stubs")
SRC = OUT / "src"
CLS = OUT / "classes"

# PacketEvents models each packet type as an instance of a nested class, and the plugin does
# `PacketTypeCommon type = event.getPacketType(); type == PacketType.Play.Server.CHUNK_DATA`,
# so Server/Client have to be classes carrying their own constants.
SERVER = [
    "ATTACH_ENTITY", "BLOCK_CHANGE", "BLOCK_ENTITY_DATA", "CHUNK_DATA", "DESTROY_ENTITIES",
    "ENTITY_ANIMATION", "ENTITY_EFFECT", "ENTITY_EQUIPMENT", "ENTITY_HEAD_LOOK",
    "ENTITY_METADATA", "ENTITY_MOVEMENT", "ENTITY_RELATIVE_MOVE",
    "ENTITY_RELATIVE_MOVE_AND_ROTATION", "ENTITY_ROTATION", "ENTITY_STATUS", "ENTITY_TELEPORT",
    "ENTITY_VELOCITY", "HURT_ANIMATION", "NAMED_SOUND_EFFECT", "OPEN_SIGN_EDITOR",
    "PLAYER_INFO_REMOVE", "PLAYER_INFO_UPDATE", "REMOVE_ENTITY_EFFECT", "SET_PASSENGERS",
    "SPAWN_ENTITY", "SPAWN_PLAYER", "SPAWN_EXPERIENCE_ORB", "SOUND_EFFECT", "UPDATE_ATTRIBUTES",
    "SYSTEM_CHAT_MESSAGE", "RESPAWN", "JOIN_GAME", "KEEP_ALIVE", "PING", "DISCONNECT",
]
CLIENT = [
    "UPDATE_SIGN", "INTERACT_ENTITY", "PLAYER_INPUT", "PLAYER_ACTION", "KEEP_ALIVE",
    "CLIENT_SETTINGS", "INTERACT_ITEM", "HELD_ITEM_CHANGE", "TELEPORT_CONFIRM",
]

FILES = {}

FILES["com/github/retrooper/packetevents/protocol/packettype/PacketType.java"] = """
package com.github.retrooper.packetevents.protocol.packettype;
/** Compile-only stub. */
public final class PacketType {

    public static final class Play {
""" + f"""        public static final class Server extends PacketTypeCommon {{
            public static final Server INSTANCE = new Server();
    """ + "\n".join(f"        public static final Server {c} = new Server();" for c in SERVER) + """
        }
""" + f"""        public static final class Client extends PacketTypeCommon {{
            public static final Client INSTANCE = new Client();
    """ + "\n".join(f"        public static final Client {c} = new Client();" for c in CLIENT) + """
        }
    }

    public static final class Configuration {
        public static final class Server extends PacketTypeCommon { }
        public static final class Client extends PacketTypeCommon { }
    }

    public static final class Status {
        public static final class Server extends PacketTypeCommon { }
        public static final class Client extends PacketTypeCommon { }
    }
}
"""

FILES["com/github/retrooper/packetevents/protocol/world/chunk/ChunkColumn.java"] = """
package com.github.retrooper.packetevents.protocol.world.chunk;
/** Compile-only stub. */
public class ChunkColumn {
    public int getX() { return 0; }
    public int getZ() { return 0; }
    public Object getChunk(int sectionY) { return null; }
    public void setChunk(int sectionY, Object chunk) { }
}
"""

FILES["com/github/retrooper/packetevents/protocol/sound/Sound.java"] = """
package com.github.retrooper.packetevents.protocol.sound;
/** Compile-only stub. */
public class Sound {
    public Sound(String key) { }
    public String getKey() { return ""; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerSoundEffect.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.sound.Sound;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerSoundEffect extends PacketWrapper<WrapperPlayServerSoundEffect> {
    public WrapperPlayServerSoundEffect(PacketSendEvent event) { super(event); }
    public WrapperPlayServerSoundEffect(Sound sound, Object category, double x, double y, double z,
                                        float volume, float pitch) { super(); }
    public Sound getSound() { return null; }
    public void setSound(Sound sound) { }
    public Object getCategory() { return null; }
    public void setCategory(Object category) { }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerEntityTeleport.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.world.Location;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerEntityTeleport extends PacketWrapper<WrapperPlayServerEntityTeleport> {
    public WrapperPlayServerEntityTeleport(PacketSendEvent event) { super(event); }
    public WrapperPlayServerEntityTeleport(int entityId, Location location, boolean onGround) { super(); }
    public int getEntityId() { return 0; }
    public Location getLocation() { return null; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerSpawnPlayer.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.world.Location;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerSpawnPlayer extends PacketWrapper<WrapperPlayServerSpawnPlayer> {
    public WrapperPlayServerSpawnPlayer(PacketSendEvent event) { super(event); }
    public WrapperPlayServerSpawnPlayer(int entityId, java.util.UUID uuid, Location location) { super(); }
    public int getEntityId() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerChunkData.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.world.chunk.ChunkColumn;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerChunkData extends PacketWrapper<WrapperPlayServerChunkData> {
    public WrapperPlayServerChunkData(PacketSendEvent event) { super(event); }
    public WrapperPlayServerChunkData(ChunkColumn column) { super(); }
    public ChunkColumn getColumn() { return new ChunkColumn(); }
    public void setColumn(ChunkColumn column) { }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerEntityEffect.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerEntityEffect extends PacketWrapper<WrapperPlayServerEntityEffect> {
    public WrapperPlayServerEntityEffect(PacketSendEvent event) { super(event); }
    public WrapperPlayServerEntityEffect(int entityId, Object effectType, int amplifier, int duration,
                                         byte flags) { super(); }
    public int getEntityId() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerRemoveEntityEffect.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerRemoveEntityEffect extends PacketWrapper<WrapperPlayServerRemoveEntityEffect> {
    public WrapperPlayServerRemoveEntityEffect(PacketSendEvent event) { super(event); }
    public WrapperPlayServerRemoveEntityEffect(int entityId, Object effectType) { super(); }
    public int getEntityId() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/client/WrapperPlayClientUpdateSign.java"] = """
package com.github.retrooper.packetevents.wrapper.play.client;
import com.github.retrooper.packetevents.event.PacketReceiveEvent;
import com.github.retrooper.packetevents.util.Vector3i;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayClientUpdateSign extends PacketWrapper<WrapperPlayClientUpdateSign> {
    public WrapperPlayClientUpdateSign(PacketReceiveEvent event) { super(event); }
    public Vector3i getBlockPosition() { return new Vector3i(0, 0, 0); }
    public String[] getTextLines() { return new String[4]; }
    public boolean isFrontText() { return true; }
}
"""

FILES["com/github/retrooper/packetevents/protocol/nbt/NBTList.java"] = """
package com.github.retrooper.packetevents.protocol.nbt;
import java.util.List;
/** Compile-only stub. */
public class NBTList<T extends NBT> extends NBT {
    public NBTList(List<T> tags, NBTType<T> type) { }
    public NBTList(List<T> tags) { }
    public NBTList(NBTType<?> type, List<? extends NBT> items) { }
    public List<T> getTags() { return List.of(); }
    public void addTag(NBT tag) { }
    @Override public NBTType<?> getType() { return NBTType.LIST; }
}
"""

FILES["com/github/retrooper/packetevents/protocol/nbt/NBTCompound.java"] = """
package com.github.retrooper.packetevents.protocol.nbt;
import java.util.Map;
/** Compile-only stub. */
public class NBTCompound extends NBT {
    public NBTCompound() { }
    public NBTCompound(Map<String, NBT> tags) { }
    public NBTCompound setTag(String name, NBT tag) { return this; }
    public NBT getTagOrNull(String name) { return null; }
    public Map<String, NBT> getTags() { return Map.of(); }
    @Override public NBTType<?> getType() { return NBTType.COMPOUND; }
}
"""

FILES["com/github/retrooper/packetevents/protocol/player/User.java"] = """
package com.github.retrooper.packetevents.protocol.player;
/** Compile-only stub. */
public interface User {
    void sendPacket(Object packet);
    int getEntityId();
    UserProfile getProfile();
    void setProfile(UserProfile profile);
    String getName();
}
"""

FILES["com/github/retrooper/packetevents/protocol/player/UserProfile.java"] = """
package com.github.retrooper.packetevents.protocol.player;
/** Compile-only stub. */
public class UserProfile {
    public UserProfile(java.util.UUID uuid, String name) { }
    public java.util.UUID getUUID() { return null; }
    public String getName() { return ""; }
}
"""

# -- WorldEdit: drop the WE5-era top-level Region, take the modern shape -------
legacy = SRC / "com/sk89q/worldedit/Region.java"
if legacy.exists():
    legacy.unlink()

FILES["com/sk89q/worldedit/EditSession.java"] = """
package com.sk89q.worldedit;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.function.operation.Operation;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.regions.Region;
import com.sk89q.worldedit.world.World;
import com.sk89q.worldedit.world.block.BlockState;
/** Compile-only stub. */
public class EditSession implements Extent, AutoCloseable {
    public EditSession(World world) { }
    public EditSession(World world, int maxBlocks) { }
    public World getWorld() { return null; }
    public void setBlock(int x, int y, int z, BlockState block) { }
    public BlockState getBlock(int x, int y, int z) { return null; }
    public Operation setBlocks(Region region, BlockState block) { return null; }
    public int size() { return 0; }
    public void flushSession() { }
    public void close() { }
    public UndoContext getUndoContext() { return null; }
    @Override public BlockState getBlock(BlockVector3 position) { return null; }
    @Override public boolean setBlock(BlockVector3 position, BlockState block) { return false; }
    /** Compile-only stub. */
    public static class UndoContext {
        public void close() { }
    }
}
"""

FILES["com/sk89q/worldedit/WorldEdit.java"] = """
package com.sk89q.worldedit;
import com.sk89q.worldedit.util.PropertiesConfiguration;
import com.sk89q.worldedit.world.World;
/** Compile-only stub. */
public final class WorldEdit {
    public static WorldEdit getInstance() { return new WorldEdit(); }
    public static boolean isInitialized() { return true; }
    public PropertiesConfiguration getConfiguration() { return new PropertiesConfiguration(); }
    public EditSessionBuilder newEditSessionBuilder() { return new EditSessionBuilder(); }
    /** Compile-only stub. */
    public static class EditSessionBuilder {
        public EditSessionBuilder world(World world) { return this; }
        public EditSessionBuilder maxBlocks(int maxBlocks) { return this; }
        public EditSessionBuilder changeSetLimit(int limit) { return this; }
        public EditSession build() { return new EditSession(null); }
    }
}
"""

FILES["com/sk89q/worldedit/extent/clipboard/io/BuiltInClipboardFormat.java"] = """
package com.sk89q.worldedit.extent.clipboard.io;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.world.World;
import java.io.InputStream;
/** Compile-only stub. */
public enum BuiltInClipboardFormat implements ClipboardFormat {
    SPONGE_SCHEMATIC, SPONGE_V2_SCHEMATIC, SPONGE_V3_SCHEMATIC, MCEDIT_SCHEMATIC, FAST_SCHEMATIC;

    @Override public ClipboardReader getReader(InputStream inputStream) { return null; }
    @Override public ClipboardWriter getWriter(java.io.OutputStream outputStream) { return null; }
    @Override public ClipboardReader getReader(InputStream inputStream, World world) { return null; }
    @Override public ClipboardWriter getWriter(java.io.OutputStream outputStream, World world) { return null; }
    @Override public String getName() { return name(); }
    @Override public String[] getAliases() { return new String[0]; }
    @Override public boolean isFormat(InputStream inputStream) { return false; }
    @Override public Clipboard read(InputStream inputStream) { return null; }
    @Override public Clipboard read(InputStream inputStream, World world) { return null; }
}
"""

FILES["com/sk89q/worldedit/extent/clipboard/io/ClipboardFormat.java"] = """
package com.sk89q.worldedit.extent.clipboard.io;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.world.World;
import java.io.InputStream;
import java.io.OutputStream;
/** Compile-only stub. */
public interface ClipboardFormat {
    ClipboardReader getReader(InputStream inputStream);
    ClipboardWriter getWriter(OutputStream outputStream);
    ClipboardReader getReader(InputStream inputStream, World world);
    ClipboardWriter getWriter(OutputStream outputStream, World world);
    String getName();
    String[] getAliases();
    boolean isFormat(InputStream inputStream);
    Clipboard read(InputStream inputStream);
    Clipboard read(InputStream inputStream, World world);
}
"""

FILES["com/sk89q/worldedit/session/ClipboardHolder.java"] = """
package com.sk89q.worldedit.session;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.function.operation.Operation;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.world.World;
/** Compile-only stub. */
public class ClipboardHolder {
    public ClipboardHolder(Clipboard clipboard) { }
    public Clipboard getClipboard() { return null; }
    public void setTransform(Object transform) { }
    public PasteBuilder createPaste(Extent extent) { return new PasteBuilder(); }
    public PasteBuilder createPaste(World world) { return new PasteBuilder(); }
    /** Compile-only stub. */
    public static class PasteBuilder {
        public PasteBuilder to(BlockVector3 position) { return this; }
        public PasteBuilder ignoreAirBlocks(boolean ignore) { return this; }
        public PasteBuilder copyEntities(boolean copy) { return this; }
        public PasteBuilder copyBiomes(boolean copy) { return this; }
        public Operation build() { return null; }
    }
}
"""

FILES["com/sk89q/worldedit/world/block/BlockTypes.java"] = """
package com.sk89q.worldedit.world.block;
/** Compile-only stub. */
public final class BlockTypes {
    public static final BlockType AIR = new BlockType();
    public static final BlockType STONE = new BlockType();
    public static final BlockType BEDROCK = new BlockType();
    public static final BlockType DIRT = new BlockType();
    public static final BlockType GRASS_BLOCK = new BlockType();
    public static final BlockType SAND = new BlockType();
    public static final BlockType SANDSTONE = new BlockType();
    public static final BlockType RED_SAND = new BlockType();
    public static final BlockType RED_SANDSTONE = new BlockType();
    public static final BlockType WATER = new BlockType();
}
"""

FILES["com/github/retrooper/packetevents/protocol/sound/Sounds.java"] = """
package com.github.retrooper.packetevents.protocol.sound;
/** Compile-only stub. */
public final class Sounds {
    public static final Sound ITEM_TRIDENT_THUNDER = new Sound("item.trident.thunder");
    public static final Sound ENTITY_PLAYER_HURT = new Sound("entity.player.hurt");
    public static final Sound ENTITY_GENERIC_EXPLODE = new Sound("entity.generic.explode");
    public static final Sound BLOCK_ANVIL_LAND = new Sound("block.anvil.land");
    public static final Sound ENTITY_PLAYER_ATTACK_NODAMAGE = new Sound("entity.player.attack.nodamage");
    public static final Sound ENTITY_PLAYER_ATTACK_STRONG = new Sound("entity.player.attack.strong");
    public static final Sound ENTITY_PLAYER_ATTACK_SWEEP = new Sound("entity.player.attack.sweep");
    public static final Sound ENTITY_PLAYER_ATTACK_WEAK = new Sound("entity.player.attack.weak");
    public static final Sound ENTITY_PLAYER_ATTACK_CRIT = new Sound("entity.player.attack.crit");
    public static final Sound ENTITY_PLAYER_ATTACK_KNOCKBACK = new Sound("entity.player.attack.knockback");
}
"""

for rel, body in FILES.items():
    target = SRC / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.lstrip(), encoding="utf-8")

import shutil
shutil.rmtree(CLS, ignore_errors=True)
CLS.mkdir(parents=True, exist_ok=True)
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
    print(f"attempt {attempt} failed:\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}",
          file=sys.stderr)
else:
    raise SystemExit(1)
