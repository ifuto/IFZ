#!/usr/bin/env python3
"""WorldEdit/FAWE stubs plus the last PacketEvents gaps, so javac can check the whole tree.

Run after make_stubs.py and make_stubs2.py. The WorldEdit stub surface mirrors
FastAsyncWorldEdit's API as the arena bridge uses it (clipboard copy/paste + file IO).

Usage: python3 make_stubs3.py <out-dir>
"""
import pathlib
import subprocess
import sys

JDK = "/tmp/toolchain/x/jdk-21.0.12.1+1"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/toolchain/stubs")
SRC = OUT / "src"
CLS = OUT / "classes"

FILES = {
    "com/sk89q/worldedit/math/BlockVector3.java": """
package com.sk89q.worldedit.math;
/** Compile-only stub. */
public class BlockVector3 {
    public static BlockVector3 at(int x, int y, int z) { return new BlockVector3(); }
    public static BlockVector3 at(double x, double y, double z) { return new BlockVector3(); }
    public int getX() { return 0; }
    public int getY() { return 0; }
    public int getZ() { return 0; }
    public BlockVector3 add(int x, int y, int z) { return this; }
    public BlockVector3 subtract(int x, int y, int z) { return this; }
    public BlockVector3 withY(int y) { return this; }
}
""",
    "com/sk89q/worldedit/util/PropertiesConfiguration.java": """
package com.sk89q.worldedit.util;
/** Compile-only stub. */
public class PropertiesConfiguration {
    public int getInt(String key, int def) { return def; }
    public String getString(String key, String def) { return def; }
}
""",
    "com/sk89q/worldedit/world/block/BlockState.java": """
package com.sk89q.worldedit.world.block;
/** Compile-only stub. */
public class BlockState {
    public BlockType getBlockType() { return null; }
}
""",
    "com/sk89q/worldedit/world/block/BlockType.java": """
package com.sk89q.worldedit.world.block;
/** Compile-only stub. */
public class BlockType {
    public BlockState getDefaultState() { return new BlockState(); }
    public String getId() { return ""; }
}
""",
    "com/sk89q/worldedit/world/block/BlockTypes.java": """
package com.sk89q.worldedit.world.block;
/** Compile-only stub. */
public final class BlockTypes {
    public static final BlockType AIR = new BlockType();
    public static final BlockType STONE = new BlockType();
}
""",
    "com/sk89q/worldedit/world/World.java": """
package com.sk89q.worldedit.world;
/** Compile-only stub. */
public interface World { }
""",
    "com/sk89q/worldedit/regions/Region.java": """
package com.sk89q.worldedit.regions;
import com.sk89q.worldedit.math.BlockVector3;
/** Compile-only stub. */
public interface Region {
    BlockVector3 getMinimumPoint();
    BlockVector3 getMaximumPoint();
    boolean contains(BlockVector3 position);
}
""",
    "com/sk89q/worldedit/regions/CuboidRegion.java": """
package com.sk89q.worldedit.regions;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.world.World;
/** Compile-only stub. */
public class CuboidRegion implements Region {
    public CuboidRegion(BlockVector3 pos1, BlockVector3 pos2) { }
    public CuboidRegion(World world, BlockVector3 pos1, BlockVector3 pos2) { }
    public World getWorld() { return null; }
    public void setWorld(World world) { }
    @Override public BlockVector3 getMinimumPoint() { return null; }
    @Override public BlockVector3 getMaximumPoint() { return null; }
    @Override public boolean contains(BlockVector3 position) { return false; }
}
""",
    "com/sk89q/worldedit/extent/Extent.java": """
package com.sk89q.worldedit.extent;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.world.block.BlockState;
/** Compile-only stub. */
public interface Extent {
    BlockState getBlock(BlockVector3 position);
    boolean setBlock(BlockVector3 position, BlockState block);
}
""",
    "com/sk89q/worldedit/extent/clipboard/Clipboard.java": """
package com.sk89q.worldedit.extent.clipboard;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.regions.Region;
import com.sk89q.worldedit.world.World;
/** Compile-only stub. */
public interface Clipboard extends Extent {
    Region getRegion();
    BlockVector3 getOrigin();
    void setOrigin(BlockVector3 origin);
    World getWorld();
    BlockVector3 getMinimumPoint();
    BlockVector3 getMaximumPoint();
}
""",
    "com/sk89q/worldedit/extent/clipboard/BlockArrayClipboard.java": """
package com.sk89q.worldedit.extent.clipboard;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.regions.CuboidRegion;
import com.sk89q.worldedit.regions.Region;
import com.sk89q.worldedit.world.World;
import com.sk89q.worldedit.world.block.BlockState;
/** Compile-only stub. */
public class BlockArrayClipboard implements Clipboard {
    public BlockArrayClipboard(Region region) { }
    public BlockArrayClipboard(Region region, BlockVector3 origin) { }
    public CuboidRegion getRegion() { return null; }
    @Override public BlockVector3 getOrigin() { return null; }
    @Override public void setOrigin(BlockVector3 origin) { }
    @Override public World getWorld() { return null; }
    @Override public BlockVector3 getMinimumPoint() { return null; }
    @Override public BlockVector3 getMaximumPoint() { return null; }
    @Override public BlockState getBlock(BlockVector3 position) { return null; }
    @Override public boolean setBlock(BlockVector3 position, BlockState block) { return false; }
}
""",
    "com/sk89q/worldedit/extent/clipboard/io/ClipboardFormat.java": """
package com.sk89q.worldedit.extent.clipboard.io;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.world.World;
import java.io.InputStream;
import java.io.OutputStream;
/** Compile-only stub. */
public abstract class ClipboardFormat {
    public ClipboardReader getReader(InputStream inputStream) { return null; }
    public ClipboardWriter getWriter(OutputStream outputStream) { return null; }
    public ClipboardReader getReader(InputStream inputStream, World world) { return null; }
    public ClipboardWriter getWriter(OutputStream outputStream, World world) { return null; }
    public String getName() { return ""; }
    public String[] getAliases() { return new String[0]; }
    public boolean isFormat(InputStream inputStream) { return false; }
    public abstract Clipboard read(InputStream inputStream);
    public abstract Clipboard read(InputStream inputStream, World world);
}
""",
    "com/sk89q/worldedit/extent/clipboard/io/BuiltInClipboardFormat.java": """
package com.sk89q.worldedit.extent.clipboard.io;
/** Compile-only stub. */
public enum BuiltInClipboardFormat {
    SPONGE_SCHEMATIC, MCEDIT_SCHEMATIC, FAST_SCHEMATIC;
    public ClipboardFormat getFormat() { return null; }
}
""",
    "com/sk89q/worldedit/extent/clipboard/io/ClipboardReader.java": """
package com.sk89q.worldedit.extent.clipboard.io;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import java.io.IOException;
/** Compile-only stub. */
public interface ClipboardReader extends AutoCloseable {
    Clipboard read() throws IOException;
    @Override void close() throws IOException;
}
""",
    "com/sk89q/worldedit/extent/clipboard/io/ClipboardWriter.java": """
package com.sk89q.worldedit.extent.clipboard.io;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import java.io.IOException;
/** Compile-only stub. */
public interface ClipboardWriter extends AutoCloseable {
    void write(Clipboard clipboard) throws IOException;
    @Override void close() throws IOException;
}
""",
    "com/sk89q/worldedit/extent/clipboard/io/ClipboardFormats.java": """
package com.sk89q.worldedit.extent.clipboard.io;
import java.io.File;
/** Compile-only stub. */
public final class ClipboardFormats {
    public static ClipboardFormat findByAlias(String alias) { return null; }
    public static ClipboardFormat findByFile(File file) { return null; }
    public static ClipboardFormat findByName(String name) { return null; }
    public static ClipboardFormat[] getFormats() { return new ClipboardFormat[0]; }
}
""",
    "com/sk89q/worldedit/function/operation/Operation.java": """
package com.sk89q.worldedit.function.operation;
/** Compile-only stub. */
public interface Operation {
    Operation resume(Object runner);
    void cancel();
    boolean isCancelled();
}
""",
    "com/sk89q/worldedit/function/operation/Operations.java": """
package com.sk89q.worldedit.function.operation;
/** Compile-only stub. */
public final class Operations {
    public static void complete(Operation operation) { }
    public static void completeLegacy(Operation operation) { }
    public static void completeSmart(Operation operation) { }
}
""",
    "com/sk89q/worldedit/function/operation/ForwardExtentCopy.java": """
package com.sk89q.worldedit.function.operation;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.regions.Region;
/** Compile-only stub. */
public class ForwardExtentCopy implements Operation {
    public ForwardExtentCopy(Extent source, Region region, Extent destination, BlockVector3 destinationPosition) { }
    public void setCopyingEntities(boolean copyingEntities) { }
    public void setCopyBiomeType(boolean copyBiomeType) { }
    public void setIgnoreAirBlocks(boolean ignoreAirBlocks) { }
    @Override public Operation resume(Object runner) { return this; }
    @Override public void cancel() { }
    @Override public boolean isCancelled() { return false; }
}
""",
    "com/sk89q/worldedit/EditSession.java": """
package com.sk89q.worldedit;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.function.operation.Operation;
import com.sk89q.worldedit.math.BlockVector3;
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
""",
    "com/sk89q/worldedit/Region.java": """
package com.sk89q.worldedit;
/** Compile-only stub for the legacy top-level Region reference. */
public interface Region extends com.sk89q.worldedit.regions.Region { }
""",
    "com/sk89q/worldedit/session/ClipboardHolder.java": """
package com.sk89q.worldedit.session;
import com.sk89q.worldedit.extent.clipboard.Clipboard;
import com.sk89q.worldedit.extent.Extent;
import com.sk89q.worldedit.function.operation.Operation;
import com.sk89q.worldedit.math.BlockVector3;
import com.sk89q.worldedit.world.World;
/** Compile-only stub. */
public class ClipboardHolder {
    public ClipboardHolder(Clipboard clipboard) { }
    public Clipboard getClipboard() { return null; }
    public void setTransform(Object transform) { }
    public Operation createPaste(World world, BlockVector3 position) { return null; }
    public Operation createPaste(Extent extent, BlockVector3 position) { return null; }
}
""",
    "com/sk89q/worldedit/bukkit/BukkitAdapter.java": """
package com.sk89q.worldedit.bukkit;
import com.sk89q.worldedit.world.World;
import com.sk89q.worldedit.world.block.BlockState;
/** Compile-only stub. */
public final class BukkitAdapter {
    public static World adapt(org.bukkit.World world) { return null; }
    public static org.bukkit.World adapt(World world) { return null; }
    public static BlockState adapt(org.bukkit.block.data.BlockData data) { return null; }
    public static org.bukkit.block.data.BlockData adapt(BlockState state) { return null; }
    public static com.sk89q.worldedit.util.PropertiesConfiguration adaptProperties() { return null; }
}
""",
    "com/sk89q/worldedit/WorldEdit.java": """
package com.sk89q.worldedit;
/** Compile-only stub. */
public final class WorldEdit {
    public static WorldEdit getInstance() { return null; }
    public static boolean isInitialized() { return false; }
    public com.sk89q.worldedit.util.PropertiesConfiguration getConfiguration() { return null; }
}
""",
}

# Last PacketEvents gaps (all in files this session did not modify).
FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerEntityHeadLook.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerEntityHeadLook extends PacketWrapper<WrapperPlayServerEntityHeadLook> {
    public WrapperPlayServerEntityHeadLook(PacketSendEvent event) { super(event); }
    public WrapperPlayServerEntityHeadLook(int entityId, float headYaw) { super(); }
    public int getEntityId() { return 0; }
    public float getHeadYaw() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerSoundEffect.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerSoundEffect extends PacketWrapper<WrapperPlayServerSoundEffect> {
    public WrapperPlayServerSoundEffect(PacketSendEvent event) { super(event); }
    public WrapperPlayServerSoundEffect(Object sound, Object category, double x, double y, double z,
                                        float volume, float pitch) { super(); }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerEntityAnimation.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerEntityAnimation extends PacketWrapper<WrapperPlayServerEntityAnimation> {
    /** Compile-only stub. */
    public enum EntityAnimationType { SWING_MAIN_ARM, HURT, WAKE_UP, SWING_OFF_HAND, CRITICAL_EFFECT, MAGIC_CRITICAL_EFFECT }
    public WrapperPlayServerEntityAnimation(PacketSendEvent event) { super(event); }
    public WrapperPlayServerEntityAnimation(int entityId, EntityAnimationType type) { super(); }
    public int getEntityId() { return 0; }
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
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerHurtAnimation.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerHurtAnimation extends PacketWrapper<WrapperPlayServerHurtAnimation> {
    public WrapperPlayServerHurtAnimation(PacketSendEvent event) { super(event); }
    public WrapperPlayServerHurtAnimation(int entityId, float yaw) { super(); }
    public int getEntityId() { return 0; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerOpenSignEditor.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.util.Vector3i;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerOpenSignEditor extends PacketWrapper<WrapperPlayServerOpenSignEditor> {
    public WrapperPlayServerOpenSignEditor(PacketSendEvent event) { super(event); }
    public WrapperPlayServerOpenSignEditor(Vector3i position) { super(); }
    public WrapperPlayServerOpenSignEditor(Vector3i position, boolean frontSide) { super(); }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerBlockEntityData.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.nbt.NBTCompound;
import com.github.retrooper.packetevents.util.Vector3i;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerBlockEntityData extends PacketWrapper<WrapperPlayServerBlockEntityData> {
    public WrapperPlayServerBlockEntityData(PacketSendEvent event) { super(event); }
    public WrapperPlayServerBlockEntityData(Vector3i position, Object type, NBTCompound nbt) { super(); }
    public Vector3i getBlockPosition() { return null; }
    public NBTCompound getNBT() { return null; }
}
"""

FILES["com/github/retrooper/packetevents/wrapper/play/server/WrapperPlayServerBlockChange.java"] = """
package com.github.retrooper.packetevents.wrapper.play.server;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.util.Vector3i;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerBlockChange extends PacketWrapper<WrapperPlayServerBlockChange> {
    public WrapperPlayServerBlockChange(PacketSendEvent event) { super(event); }
    public WrapperPlayServerBlockChange(Vector3i position, Object blockState) { super(); }
    public Vector3i getBlockPosition() { return null; }
}
"""

FILES["com/github/retrooper/packetevents/protocol/world/blockentity/BlockEntityTypes.java"] = """
package com.github.retrooper.packetevents.protocol.world.blockentity;
/** Compile-only stub. */
public final class BlockEntityTypes {
    public static final Object SIGN = new Object();
    public static final Object HANGING_SIGN = new Object();
    public static final Object BANNER = new Object();
}
"""

FILES["com/github/retrooper/packetevents/protocol/entity/EntityType.java"] = """
package com.github.retrooper.packetevents.protocol.entity;
/** Compile-only stub. */
public class EntityType {
    public static EntityType PLAYER = new EntityType();
    public static EntityType ARMOR_STAND = new EntityType();
    public static EntityType getById(int id) { return null; }
    public static EntityType getByName(String name) { return null; }
}
"""

for rel, body in FILES.items():
    target = SRC / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.lstrip(), encoding="utf-8")

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
