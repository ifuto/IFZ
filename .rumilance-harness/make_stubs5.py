#!/usr/bin/env python3
"""Entity/movement wrapper stubs that PacketEntityIds + the replay/lethal paths import.

These were part of the original base stub set; re-created on demand: every class here is
used only for its entity id (the plugin reads packets to learn who a numeric id belongs
to), so `getEntityId()` plus a PacketSendEvent constructor is the whole surface.

Usage: python3 make_stubs5.py <out-dir>
"""
import pathlib
import sys

JDK = "/tmp/toolchain/x/jdk-21.0.12.1+1"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/toolchain/stubs")
SRC = OUT / "src"
CLS = OUT / "classes"

PKG = "com.github.retrooper.packetevents.wrapper.play.server"

# クラス名 -> 追加のコンストラクタ引数(すべて int の実体 id)
WRAPPERS = {
    "WrapperPlayServerDestroyEntities": None,   # varargs 版を別に書く
    "WrapperPlayServerEntityEquipment": None,
    "WrapperPlayServerEntityMovement": None,
    "WrapperPlayServerEntityRelativeMove": None,
    "WrapperPlayServerEntityRelativeMoveAndRotation": None,
    "WrapperPlayServerEntityRotation": None,
    "WrapperPlayServerEntityVelocity": None,
    "WrapperPlayServerSetPassengers": None,
}

FILES = {}

for name in WRAPPERS:
    FILES[f"{PKG.replace('.', '/')}/{name}.java"] = f"""
package {PKG};
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class {name} extends PacketWrapper<{name}> {{
    public {name}(PacketSendEvent event) {{ super(event); }}
    public {name}(int entityId) {{ super(); }}
    public int getEntityId() {{ return 0; }}
    public void setEntityId(int entityId) {{ }}
}}
"""

# v2〜v4 はこの 2 つを event コンストラクタだけで定義している(読み取り用)。書き込み側の
# 実体 id + 中身で組む形も使うので、ここで上書きして両方持たせる。
FILES[f"{PKG.replace('.', '/')}/WrapperPlayServerEntityMetadata.java"] = f"""
package {PKG};
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.entity.data.EntityData;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
import java.util.List;
/** Compile-only stub. */
public class WrapperPlayServerEntityMetadata extends PacketWrapper<WrapperPlayServerEntityMetadata> {{
    public WrapperPlayServerEntityMetadata(PacketSendEvent event) {{ super(event); }}
    public WrapperPlayServerEntityMetadata(int entityId) {{ super(); }}
    public WrapperPlayServerEntityMetadata(int entityId, List<EntityData<?>> entityMetadata) {{ super(); }}
    public int getEntityId() {{ return 0; }}
    public List<EntityData<?>> getEntityMetadata() {{ return List.of(); }}
}}
"""

FILES[f"{PKG.replace('.', '/')}/WrapperPlayServerEntityStatus.java"] = f"""
package {PKG};
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerEntityStatus extends PacketWrapper<WrapperPlayServerEntityStatus> {{
    public WrapperPlayServerEntityStatus(PacketSendEvent event) {{ super(event); }}
    public WrapperPlayServerEntityStatus(int entityId, int status) {{ super(); }}
    public int getEntityId() {{ return 0; }}
    public int getStatus() {{ return 0; }}
}}
"""

FILES[f"{PKG.replace('.', '/')}/WrapperPlayServerDestroyEntities.java"] = f"""
package {PKG};
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.wrapper.PacketWrapper;
/** Compile-only stub. */
public class WrapperPlayServerDestroyEntities extends PacketWrapper<WrapperPlayServerDestroyEntities> {{
    public WrapperPlayServerDestroyEntities(PacketSendEvent event) {{ super(event); }}
    public WrapperPlayServerDestroyEntities(int entityId) {{ super(); }}
    public WrapperPlayServerDestroyEntities(int... entityIds) {{ super(); }}
    public int getEntityId() {{ return 0; }}
    public int[] getEntityIds() {{ return new int[0]; }}
}}
"""


def main() -> int:
    for rel, body in FILES.items():
        path = SRC / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"wrote {len(FILES)} wrapper stub(s) to {SRC}")
    # User スタブが返すものを Object ではなく User にする(getProfile() を呼ばれるため)。
    pe = SRC / "com/github/retrooper/packetevents/PacketEvents.java"
    if pe.exists():
        text = pe.read_text(encoding="utf-8")
        text = text.replace("public Object getUser(Object player) { return null; }",
                            "public User getUser(Object player) { return null; }")
        text = text.replace("public Object getUser(java.util.UUID uuid) { return null; }",
                            "public User getUser(java.util.UUID uuid) { return null; }")
        if "import com.github.retrooper.packetevents.protocol.player.User;" not in text:
            text = text.replace("import com.github.retrooper.packetevents.event.PacketListenerPriority;",
                                "import com.github.retrooper.packetevents.event.PacketListenerPriority;\n"
                                "import com.github.retrooper.packetevents.protocol.player.User;")
        pe.write_text(text, encoding="utf-8")
        print("PacketEvents stub: getUser() now returns User")
    return 0


if __name__ == "__main__":
    sys.exit(main())
