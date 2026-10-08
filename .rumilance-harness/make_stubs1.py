#!/usr/bin/env python3
"""Base compile-only stubs (v1) — the families the rest of make_stubs*.py build on.

Re-created after the workspace copy was lost: PacketEvents' *base* types (PacketEvents API,
PacketSendEvent/PacketReceiveEvent, PacketWrapper, NBT/NBTType, GameMode, Vector3i,
PacketTypeCommon) plus the core WorldEdit surface. Run FIRST, then make_stubs2/3/4.

Usage: python3 make_stubs1.py <out-dir>
"""
import pathlib
import subprocess
import sys

JDK = "/tmp/toolchain/x/jdk-21.0.12.1+1"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/toolchain/stubs")
SRC = OUT / "src"
CLS = OUT / "classes"

FILES = {}

PE = "com/github/retrooper/packetevents"

FILES[f"{PE}/PacketEvents.java"] = f"""
package {PE.replace('/', '.')};
import {PE.replace('/', '.')}.event.PacketListener;
import {PE.replace('/', '.')}.event.PacketListenerPriority;
/** Compile-only stub. */
public final class PacketEvents {{
    private static final API API_INSTANCE = new API();
    public static API getAPI() {{ return API_INSTANCE; }}
    public static void setAPI(API api) {{ }}
    public static boolean isInitialized() {{ return true; }}

    /** Compile-only stub. */
    public static final class API {{
        public EventManager getEventManager() {{ return new EventManager(); }}
        public PlayerManager getPlayerManager() {{ return new PlayerManager(); }}
    }}

    /** Compile-only stub. */
    public static final class EventManager {{
        public void registerListener(PacketListener listener, PacketListenerPriority priority) {{ }}
        public void registerListener(PacketListener listener) {{ }}
    }}

    /** Compile-only stub. */
    public static final class PlayerManager {{
        public void sendPacket(Object player, Object packet) {{ }}
        public void sendPacketSilently(Object player, Object packet) {{ }}
        public Object getUser(Object player) {{ return null; }}
        public Object getUser(java.util.UUID uuid) {{ return null; }}
    }}
}}
"""

FILES[f"{PE}/event/PacketListenerPriority.java"] = f"""
package {PE.replace('/', '.')}.event;
/** Compile-only stub. */
public enum PacketListenerPriority {{
    LOWEST, LOW, NORMAL, HIGH, HIGHEST, MONITOR;
}}
"""

FILES[f"{PE}/event/PacketSendEvent.java"] = f"""
package {PE.replace('/', '.')}.event;
import {PE.replace('/', '.')}.protocol.packettype.PacketTypeCommon;
/** Compile-only stub. */
public class PacketSendEvent {{
    public PacketSendEvent(Object user, Object player, Object packet) {{ }}
    public PacketTypeCommon getPacketType() {{ return null; }}
    public boolean isCancelled() {{ return false; }}
    public void setCancelled(boolean cancelled) {{ }}
    public Object getPlayer() {{ return null; }}
    public Object getUser() {{ return null; }}
    public Object getChannel() {{ return null; }}
}}
"""

FILES[f"{PE}/event/PacketReceiveEvent.java"] = f"""
package {PE.replace('/', '.')}.event;
import {PE.replace('/', '.')}.protocol.packettype.PacketTypeCommon;
/** Compile-only stub. */
public class PacketReceiveEvent {{
    public PacketReceiveEvent(Object user, Object player, Object packet) {{ }}
    public PacketTypeCommon getPacketType() {{ return null; }}
    public boolean isCancelled() {{ return false; }}
    public void setCancelled(boolean cancelled) {{ }}
    public Object getPlayer() {{ return null; }}
    public Object getUser() {{ return null; }}
}}
"""

FILES[f"{PE}/wrapper/PacketWrapper.java"] = f"""
package {PE.replace('/', '.')}.wrapper;
import {PE.replace('/', '.')}.event.PacketReceiveEvent;
import {PE.replace('/', '.')}.event.PacketSendEvent;
/** Compile-only stub. */
public abstract class PacketWrapper<T extends PacketWrapper<T>> {{
    public PacketWrapper() {{ }}
    public PacketWrapper(PacketSendEvent event) {{ }}
    public PacketWrapper(PacketReceiveEvent event) {{ }}
    public PacketSendEvent getSendEvent() {{ return null; }}
    public PacketReceiveEvent getReceiveEvent() {{ return null; }}
    public void writeVarInt(int value) {{ }}
    public int readVarInt() {{ return 0; }}
    public void writeString(String value) {{ }}
    public String readString() {{ return ""; }}
    public void writeBoolean(boolean value) {{ }}
    public boolean readBoolean() {{ return false; }}
    public void writeByte(int value) {{ }}
    public byte readByte() {{ return 0; }}
    public void writeInt(int value) {{ }}
    public int readInt() {{ return 0; }}
    public void writeDouble(double value) {{ }}
    public double readDouble() {{ return 0.0d; }}
    public void writeFloat(float value) {{ }}
    public float readFloat() {{ return 0.0f; }}
    public void writeLong(long value) {{ }}
    public long readLong() {{ return 0L; }}
    public void writeUUID(java.util.UUID value) {{ }}
    public java.util.UUID readUUID() {{ return null; }}
}}
"""

FILES[f"{PE}/protocol/packettype/PacketTypeCommon.java"] = f"""
package {PE.replace('/', '.')}.protocol.packettype;
/** Compile-only stub. */
public class PacketTypeCommon {{
    public String getName() {{ return getClass().getSimpleName(); }}
}}
"""

FILES[f"{PE}/protocol/player/GameMode.java"] = f"""
package {PE.replace('/', '.')}.protocol.player;
/** Compile-only stub. */
public enum GameMode {{ SURVIVAL, CREATIVE, ADVENTURE, SPECTATOR; }}
"""

FILES[f"{PE}/util/Vector3i.java"] = f"""
package {PE.replace('/', '.')}.util;
/** Compile-only stub. */
public class Vector3i {{
    public final int x;
    public final int y;
    public final int z;
    public Vector3i(int x, int y, int z) {{ this.x = x; this.y = y; this.z = z; }}
    public int getX() {{ return x; }}
    public int getY() {{ return y; }}
    public int getZ() {{ return z; }}
}}
"""

FILES[f"{PE}/protocol/nbt/NBT.java"] = f"""
package {PE.replace('/', '.')}.protocol.nbt;
/** Compile-only stub. */
public abstract class NBT {{
    public abstract NBTType<?> getType();
}}
"""

FILES[f"{PE}/protocol/nbt/NBTType.java"] = f"""
package {PE.replace('/', '.')}.protocol.nbt;
/** Compile-only stub. */
public class NBTType<T extends NBT> {{
    public static final NBTType<NBTEnd> END = new NBTType<>();
    public static final NBTType<NBTByte> BYTE = new NBTType<>();
    public static final NBTType<NBTTagShort> SHORT = new NBTType<>();
    public static final NBTType<NBTInt> INT = new NBTType<>();
    public static final NBTType<NBTLong> LONG = new NBTType<>();
    public static final NBTType<NBTFloat> FLOAT = new NBTType<>();
    public static final NBTType<NBTDouble> DOUBLE = new NBTType<>();
    public static final NBTType<NBTByteArray> BYTE_ARRAY = new NBTType<>();
    public static final NBTType<NBTString> STRING = new NBTType<>();
    public static final NBTType<NBTList<?>> LIST = new NBTType<>();
    public static final NBTType<NBTCompound> COMPOUND = new NBTType<>();
    public static final NBTType<NBTIntArray> INT_ARRAY = new NBTType<>();
    public static final NBTType<NBTLongArray> LONG_ARRAY = new NBTType<>();
    public String getName() {{ return getClass().getSimpleName(); }}

    /** Compile-only stub. */
    public static class NBTEnd extends NBT {{
        @Override public NBTType<?> getType() {{ return END; }}
    }}
    /** Compile-only stub. */
    public static class NBTTagShort extends NBT {{
        @Override public NBTType<?> getType() {{ return SHORT; }}
    }}
    /** Compile-only stub. */
    public static class NBTLong extends NBT {{
        @Override public NBTType<?> getType() {{ return LONG; }}
    }}
    /** Compile-only stub. */
    public static class NBTFloat extends NBT {{
        @Override public NBTType<?> getType() {{ return FLOAT; }}
    }}
    /** Compile-only stub. */
    public static class NBTDouble extends NBT {{
        @Override public NBTType<?> getType() {{ return DOUBLE; }}
    }}
    /** Compile-only stub. */
    public static class NBTByteArray extends NBT {{
        @Override public NBTType<?> getType() {{ return BYTE_ARRAY; }}
    }}
    /** Compile-only stub. */
    public static class NBTIntArray extends NBT {{
        @Override public NBTType<?> getType() {{ return INT_ARRAY; }}
    }}
    /** Compile-only stub. */
    public static class NBTLongArray extends NBT {{
        @Override public NBTType<?> getType() {{ return LONG_ARRAY; }}
    }}
}}
"""

FILES[f"{PE}/protocol/nbt/NBTByte.java"] = f"""
package {PE.replace('/', '.')}.protocol.nbt;
/** Compile-only stub. */
public class NBTByte extends NBT {{
    public NBTByte(byte value) {{ }}
    public byte getValue() {{ return 0; }}
    @Override public NBTType<?> getType() {{ return NBTType.BYTE; }}
}}
"""

FILES[f"{PE}/protocol/nbt/NBTInt.java"] = f"""
package {PE.replace('/', '.')}.protocol.nbt;
/** Compile-only stub. */
public class NBTInt extends NBT {{
    public NBTInt(int value) {{ }}
    public int getValue() {{ return 0; }}
    @Override public NBTType<?> getType() {{ return NBTType.INT; }}
}}
"""

FILES[f"{PE}/protocol/nbt/NBTString.java"] = f"""
package {PE.replace('/', '.')}.protocol.nbt;
/** Compile-only stub. */
public class NBTString extends NBT {{
    public NBTString(String value) {{ }}
    public String getValue() {{ return ""; }}
    @Override public NBTType<?> getType() {{ return NBTType.STRING; }}
}}
"""

FILES[f"{PE}/protocol/entity/data/EntityData.java"] = f"""
package {PE.replace('/', '.')}.protocol.entity.data;
import {PE.replace('/', '.')}.protocol.entity.EntityType;
/** Compile-only stub. */
public class EntityData<T> {{
    public EntityData(int index, EntityDataTypes.Provider<T> type, T value) {{ }}
    public EntityData(int index, EntityDataTypes.Provider<T> type) {{ }}
    public int getIndex() {{ return 0; }}
    public Object getType() {{ return null; }}
    public T getValue() {{ return null; }}
}}
"""

FILES[f"{PE}/protocol/entity/data/EntityDataTypes.java"] = f"""
package {PE.replace('/', '.')}.protocol.entity.data;
/** Compile-only stub (only the provider shape the plugin names). */
public final class EntityDataTypes {{
    private EntityDataTypes() {{ }}
    public static final Provider<Byte> BYTE = new Provider<>();
    public static final Provider<Integer> INT = new Provider<>();
    public static final Provider<Float> FLOAT = new Provider<>();
    public static final Provider<String> STRING = new Provider<>();
    public static final Provider<Boolean> BOOLEAN = new Provider<>();
    public static final Provider<Object> BLOCK_STATE = new Provider<>();
    public static final Provider<Object> ITEM_STACK = new Provider<>();
    public static final Provider<Object> COMPONENT = new Provider<>();

    /** Compile-only stub. */
    public static class Provider<T> {{ }}
}}
"""

# ---------------------------------------------------------------- WorldEdit core

WE = "com/sk89q/worldedit"

FILES[f"{WE}/math/BlockVector3.java"] = f"""
package {WE.replace('/', '.')}.math;
/** Compile-only stub. */
public class BlockVector3 {{
    public BlockVector3(int x, int y, int z) {{ }}
    public static BlockVector3 at(int x, int y, int z) {{ return new BlockVector3(x, y, z); }}
    public int getX() {{ return 0; }}
    public int getY() {{ return 0; }}
    public int getZ() {{ return 0; }}
    public int x() {{ return 0; }}
    public int y() {{ return 0; }}
    public int z() {{ return 0; }}
}}
"""

FILES[f"{WE}/regions/Region.java"] = f"""
package {WE.replace('/', '.')}.regions;
import {WE.replace('/', '.')}.math.BlockVector3;
/** Compile-only stub. */
public interface Region {{
    BlockVector3 getMinimumPoint();
    BlockVector3 getMaximumPoint();
}}
"""

FILES[f"{WE}/regions/CuboidRegion.java"] = f"""
package {WE.replace('/', '.')}.regions;
import {WE.replace('/', '.')}.math.BlockVector3;
import {WE.replace('/', '.')}.world.World;
/** Compile-only stub. */
public class CuboidRegion implements Region {{
    public CuboidRegion(World world, BlockVector3 min, BlockVector3 max) {{ }}
    public CuboidRegion(BlockVector3 min, BlockVector3 max) {{ }}
    @Override public BlockVector3 getMinimumPoint() {{ return null; }}
    @Override public BlockVector3 getMaximumPoint() {{ return null; }}
    public World getWorld() {{ return null; }}
}}
"""

FILES[f"{WE}/world/World.java"] = f"""
package {WE.replace('/', '.')}.world;
/** Compile-only stub. */
public interface World {{ }}
"""

FILES[f"{WE}/world/block/BlockState.java"] = f"""
package {WE.replace('/', '.')}.world.block;
/** Compile-only stub. */
public class BlockState {{
    public BlockType getBlockType() {{ return null; }}
    public String getId() {{ return "minecraft:air"; }}
}}
"""

FILES[f"{WE}/world/block/BlockType.java"] = f"""
package {WE.replace('/', '.')}.world.block;
/** Compile-only stub. */
public class BlockType {{
    public BlockState getDefaultState() {{ return new BlockState(); }}
}}
"""

FILES[f"{WE}/extent/Extent.java"] = f"""
package {WE.replace('/', '.')}.extent;
import {WE.replace('/', '.')}.math.BlockVector3;
import {WE.replace('/', '.')}.world.block.BlockState;
/** Compile-only stub. */
public interface Extent {{
    BlockState getBlock(BlockVector3 position);
    boolean setBlock(BlockVector3 position, BlockState block);
}}
"""

FILES[f"{WE}/extent/clipboard/Clipboard.java"] = f"""
package {WE.replace('/', '.')}.extent.clipboard;
import {WE.replace('/', '.')}.extent.Extent;
import {WE.replace('/', '.')}.math.BlockVector3;
import {WE.replace('/', '.')}.regions.Region;
/** Compile-only stub. */
public interface Clipboard extends Extent {{
    Region getRegion();
    BlockVector3 getOrigin();
}}
"""

FILES[f"{WE}/extent/clipboard/BlockArrayClipboard.java"] = f"""
package {WE.replace('/', '.')}.extent.clipboard;
import {WE.replace('/', '.')}.math.BlockVector3;
import {WE.replace('/', '.')}.regions.Region;
import {WE.replace('/', '.')}.world.block.BlockState;
/** Compile-only stub. */
public class BlockArrayClipboard implements Clipboard {{
    public BlockArrayClipboard(Region region) {{ }}
    public BlockArrayClipboard(Region region, BlockVector3 origin) {{ }}
    @Override public Region getRegion() {{ return null; }}
    @Override public BlockVector3 getOrigin() {{ return null; }}
    @Override public BlockState getBlock(BlockVector3 position) {{ return null; }}
    @Override public boolean setBlock(BlockVector3 position, BlockState block) {{ return false; }}
}}
"""

FILES[f"{WE}/extent/clipboard/io/ClipboardReader.java"] = f"""
package {WE.replace('/', '.')}.extent.clipboard.io;
import {WE.replace('/', '.')}.extent.clipboard.Clipboard;
import java.io.Closeable;
/** Compile-only stub. */
public interface ClipboardReader extends Closeable {{
    Clipboard read() throws java.io.IOException;
    @Override void close() throws java.io.IOException;
}}
"""

FILES[f"{WE}/extent/clipboard/io/ClipboardWriter.java"] = f"""
package {WE.replace('/', '.')}.extent.clipboard.io;
import {WE.replace('/', '.')}.extent.clipboard.Clipboard;
import java.io.Closeable;
/** Compile-only stub. */
public interface ClipboardWriter extends Closeable {{
    void write(Clipboard clipboard) throws java.io.IOException;
    @Override void close() throws java.io.IOException;
}}
"""

FILES[f"{WE}/extent/clipboard/io/ClipboardFormats.java"] = f"""
package {WE.replace('/', '.')}.extent.clipboard.io;
/** Compile-only stub. */
public final class ClipboardFormats {{
    private ClipboardFormats() {{ }}
    public static ClipboardFormat findByFile(java.io.File file) throws java.io.IOException {{
        return null;
    }}
    public static ClipboardFormat findByAlias(String alias) {{ return null; }}
}}
"""

FILES[f"{WE}/function/operation/Operation.java"] = f"""
package {WE.replace('/', '.')}.function.operation;
/** Compile-only stub. */
public interface Operation {{
    Operation resume(Object run);
}}
"""

FILES[f"{WE}/function/operation/Operations.java"] = f"""
package {WE.replace('/', '.')}.function.operation;
/** Compile-only stub. */
public final class Operations {{
    private Operations() {{ }}
    public static void complete(Operation operation) throws Exception {{ }}
    public static void complete(Operation operation, int attempts) throws Exception {{ }}
}}
"""

FILES[f"{WE}/function/operation/ForwardExtentCopy.java"] = f"""
package {WE.replace('/', '.')}.function.operation;
import {WE.replace('/', '.')}.extent.Extent;
import {WE.replace('/', '.')}.math.BlockVector3;
import {WE.replace('/', '.')}.regions.Region;
/** Compile-only stub. */
public class ForwardExtentCopy implements Operation {{
    public ForwardExtentCopy(Extent extent, Region region, Extent destination, BlockVector3 to) {{ }}
    public void setCopyingEntities(boolean copyingEntities) {{ }}
    public void setCopyingBiomes(boolean copyingBiomes) {{ }}
    @Override public Operation resume(Object run) {{ return null; }}
}}
"""

FILES[f"{WE}/util/PropertiesConfiguration.java"] = f"""
package {WE.replace('/', '.')}.util;
/** Compile-only stub. */
public class PropertiesConfiguration {{
    public int getMaxBrushRadius() {{ return 0; }}
    public void setMaxBrushRadius(int value) {{ }}
}}
"""

FILES[f"{WE}/session/PasteBuilder.java"] = f"""
package {WE.replace('/', '.')}.session;
import {WE.replace('/', '.')}.function.operation.Operation;
import {WE.replace('/', '.')}.math.BlockVector3;
/** Compile-only stub. */
public class PasteBuilder {{
    public PasteBuilder to(BlockVector3 to) {{ return this; }}
    public PasteBuilder ignoreAirBlocks(boolean ignoreAirBlocks) {{ return this; }}
    public PasteBuilder copyEntities(boolean copyEntities) {{ return this; }}
    public Operation build() {{ return null; }}
}}
"""

FILES[f"{WE}/session/ClipboardHolder.java"] = f"""
package {WE.replace('/', '.')}.session;
import {WE.replace('/', '.')}.EditSession;
import {WE.replace('/', '.')}.extent.clipboard.Clipboard;
/** Compile-only stub. */
public class ClipboardHolder {{
    public ClipboardHolder(Clipboard clipboard) {{ }}
    public Clipboard getClipboard() {{ return null; }}
    public PasteBuilder createPaste(EditSession editSession) {{ return new PasteBuilder(); }}
}}
"""

FILES[f"{WE}/bukkit/BukkitAdapter.java"] = f"""
package {WE.replace('/', '.')}.bukkit;
/** Compile-only stub. */
public final class BukkitAdapter {{
    private BukkitAdapter() {{ }}
    public static com.sk89q.worldedit.world.World adapt(org.bukkit.World world) {{ return null; }}
    public static org.bukkit.World adapt(com.sk89q.worldedit.world.World world) {{ return null; }}
    public static com.sk89q.worldedit.world.block.BlockState adapt(org.bukkit.block.Block block) {{ return null; }}
}}
"""

FILES[f"{WE}/world/block/BlockTypes.java"] = f"""
package {WE.replace('/', '.')}.world.block;
/** Compile-only stub (v4 overwrites this with the real-shaped enum list). */
public final class BlockTypes {{
    private BlockTypes() {{ }}
    public static final BlockType AIR = new BlockType();
    public static final BlockType STONE = new BlockType();
    public static final BlockType GRASS_BLOCK = new BlockType();
    public static final BlockType DIRT = new BlockType();
}}
"""


# リポジトリ内の最小スタブ(NotNull/Nullable など)も樹に取り込む。gradle の
# annotations jar が無い環境で full-tree コンパイルを通すのに必要。
REPO_STUBS = pathlib.Path("/home/user/RumilancePractice/tools/parity-runner/stubs")


def import_repo_stubs() -> int:
    if not REPO_STUBS.is_dir():
        return 0
    copied = 0
    for path in REPO_STUBS.rglob("*.java"):
        rel = path.relative_to(REPO_STUBS)
        target = SRC / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != path.read_text(encoding="utf-8"):
            target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        copied += 1
    return copied


def main() -> int:
    copied = import_repo_stubs()
    if copied:
        print(f"imported {copied} stub(s) from tools/parity-runner/stubs")
    for rel, body in FILES.items():
        path = SRC / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"wrote {len(FILES)} stub source file(s) to {SRC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
