#!/usr/bin/env python3
"""Split the PacketEvents half of LethalPresentationService into its own class (#16).

Usage: python3 fixes2.py [repo-root]

Why: LethalPresentationService implemented PacketListener, and a class that implements a
PacketEvents interface cannot even be CLASS-LOADED on a server without PacketEvents - the JVM
resolves interfaces while linking the class, before the constructor's
`getPlugin("packetevents") != null` check ever runs. Guarding at call time was therefore
useless: the service died with NoClassDefFoundError on a PE-less server. All PE types now live
in a package-private class that is only loaded from inside the presence check.

Idempotent: every step skips itself when the split is already in place.
"""
import pathlib
import sys

REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path("/home/user/RumilancePractice")

SERVICE = "src/main/java/com/rumilance/practice/combat/LethalPresentationService.java"
PACKETS = "src/main/java/com/rumilance/practice/combat/LethalPresentationPackets.java"

applied = []
skipped = []
failed = []


def patch(rel, old, new, label, marker=None):
    path = REPO / rel
    text = path.read_text(encoding="utf-8")
    already = (new in text) if (old in new) else (old not in text)
    if already and (marker is None or marker in text):
        skipped.append(label)
        return
    if text.count(old) != 1:
        failed.append(f"{label}: anchor x{text.count(old)}, want 1")
        return
    path.write_text(text.replace(old, new), encoding="utf-8")
    applied.append(label)


# 1. the packets class itself
packets_file = REPO / PACKETS
if packets_file.exists() and "class LethalPresentationPackets" in packets_file.read_text(encoding="utf-8"):
    skipped.append("packets class")
else:
    packets_file.write_text('''package com.rumilance.practice.combat;

import com.github.retrooper.packetevents.PacketEvents;
import com.github.retrooper.packetevents.event.PacketListener;
import com.github.retrooper.packetevents.event.PacketListenerPriority;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.packettype.PacketType;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerDestroyEntities;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerEntityStatus;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerSpawnPlayer;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;

import java.util.Set;
import java.util.UUID;

/**
 * PacketEvents side of {@link LethalPresentationService}: the forged death animation, the destroy
 * packet that drops the victim's entity (and hit box) from the killer's client, and the spawn
 * packet cut-off that keeps it from coming back.
 *
 * <p>Every PacketEvents type the feature needs lives here and nothing else references this class
 * except {@link LethalPresentationService}, which only ever touches it from inside a
 * {@code getPlugin("packetevents") != null} check. That is what makes PacketEvents a true soft
 * dependency: the JVM links interfaces while class-loading, so a class that implements
 * {@link PacketListener} can never be loaded on a server without the plugin - guarding at call
 * time is too late.</p>
 */
final class LethalPresentationPackets {

    private LethalPresentationPackets() {
    }

    /** Registers the spawn-packet filter. Only called when PacketEvents is present. */
    static void register(LethalPresentationService service, Plugin plugin) {
        PacketEvents.getAPI().getEventManager().registerListener(
                new Filter(service, plugin), PacketListenerPriority.NORMAL);
    }

    /** The forged death animation for the killer's client. */
    static void sendDeathStatus(Player killer, int victimEntityId) {
        PacketEvents.getAPI().getPlayerManager().sendPacket(killer,
                new WrapperPlayServerEntityStatus(victimEntityId, LethalPresentationService.DEATH_STATUS));
    }

    /** Drops the victim's entity - model and hit box - from the killer's client. */
    static void sendDestroy(Player killer, int targetEntityId) {
        PacketEvents.getAPI().getPlayerManager().sendPacket(killer,
                new WrapperPlayServerDestroyEntities(targetEntityId));
    }

    /**
     * The packet cut-off: while a victim is staged as dead for a viewer, their spawn packet never
     * reaches that viewer, so no chunk reload or re-track can bring them back.
     */
    private static final class Filter implements PacketListener {

        private final LethalPresentationService service;
        private final Plugin plugin;

        private Filter(LethalPresentationService service, Plugin plugin) {
            this.service = service;
            this.plugin = plugin;
        }

        @Override
        public void onPacketSend(PacketSendEvent event) {
            if (event.getPacketType() != PacketType.Play.Server.SPAWN_PLAYER) {
                return;
            }
            Object receiver = event.getPlayer();
            if (!(receiver instanceof Player viewer)) {
                return;
            }
            Set<Integer> ids = service.suppressedFor(viewer.getUniqueId());
            if (ids == null || ids.isEmpty()) {
                return;
            }
            try {
                if (ids.contains(new WrapperPlayServerSpawnPlayer(event).getEntityId())) {
                    event.setCancelled(true);
                }
            } catch (Throwable t) {
                service.logPacketFailure("spawn filter failed", t);
            }
        }
    }
}
''', encoding="utf-8")
    applied.append("packets class")

# 2. the service stops implementing PacketListener and stops naming PE types
patch(SERVICE,
      """import com.github.retrooper.packetevents.PacketEvents;
import com.github.retrooper.packetevents.event.PacketListener;
import com.github.retrooper.packetevents.event.PacketListenerPriority;
import com.github.retrooper.packetevents.event.PacketSendEvent;
import com.github.retrooper.packetevents.protocol.packettype.PacketType;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerDestroyEntities;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerEntityStatus;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerSpawnPlayer;
import org.bukkit.Bukkit;""",
      """import org.bukkit.Bukkit;""",
      "service: PE imports dropped")

patch(SERVICE,
      """public final class LethalPresentationService implements Listener, PacketListener {""",
      """public final class LethalPresentationService implements Listener {""",
      "service: no longer implements PacketListener")

patch(SERVICE,
      """                PacketEvents.getAPI().getEventManager()
                        .registerListener(this, PacketListenerPriority.NORMAL);""",
      """                // The packets class names PacketEvents types, so it may only ever be
                // class-loaded from inside this presence check and inside the catch.
                LethalPresentationPackets.register(this, plugin);""",
      "service: listener registration goes through the packets class")

patch(SERVICE,
      """                    PacketEvents.getAPI().getPlayerManager().sendPacket(killer,
                            new WrapperPlayServerDestroyEntities(target.getEntityId()));""",
      """                    LethalPresentationPackets.sendDestroy(killer, target.getEntityId());""",
      "service: destroy packet goes through the packets class")

patch(SERVICE,
      """            PacketEvents.getAPI().getPlayerManager().sendPacket(killer,
                    new WrapperPlayServerEntityStatus(victim.getEntityId(), DEATH_STATUS));""",
      """            LethalPresentationPackets.sendDeathStatus(killer, victim.getEntityId());""",
      "service: death status goes through the packets class")

# 3. the spawn filter body moves out; the service keeps package-private accessors for it
old_filter = '''    /**
     * The packet cut-off: while a victim is staged as dead for a viewer, their spawn packet never
     * reaches that viewer, so no chunk reload or re-track can bring them back.
     */
    @Override
    public void onPacketSend(PacketSendEvent event) {
        if (suppressed.isEmpty()
                || event.getPacketType() != PacketType.Play.Server.SPAWN_PLAYER) {
            return;
        }
        Object receiver = event.getPlayer();
        if (!(receiver instanceof Player viewer)) {
            return;
        }
        Set<Integer> ids = suppressed.get(viewer.getUniqueId());
        if (ids == null || ids.isEmpty()) {
            return;
        }
        try {
            if (ids.contains(new WrapperPlayServerSpawnPlayer(event).getEntityId())) {
                event.setCancelled(true);
            }
        } catch (Throwable t) {
            plugin.getLogger().log(Level.FINE, "[LethalFx] spawn filter failed", t);
        }
    }'''
new_filter = '''    /** Entity ids this viewer must not receive spawn packets for (read by the packets class). */
    Set<Integer> suppressedFor(UUID killerId) {
        return suppressed.get(killerId);
    }

    /** Logs a packet-side failure without ever letting it escape into the packet pipeline. */
    void logPacketFailure(String message, Throwable error) {
        plugin.getLogger().log(Level.FINE, "[LethalFx] " + message, error);
    }'''
patch(SERVICE, old_filter, new_filter, "service: spawn filter body replaced by accessors")

# 4. the class javadoc used to describe the pre-split design
patch(SERVICE,
      """ * <p>PacketEvents is a soft dependency: without it only step 2 is lost, and a missing listener
 * simply means the victim can reappear later rather than the feature breaking.</p>""",
      """ * <p>PacketEvents is a soft dependency: without it only step 2 is lost, and a missing listener
 * simply means the victim can reappear later rather than the feature breaking. Every PacketEvents
 * type this feature needs lives in {@link LethalPresentationPackets}, because a class that
 * implements a PacketEvents interface cannot even be class-loaded on a server without the plugin -
 * the JVM resolves the interface before the constructor's presence check ever runs.</p>""",
      "service: javadoc points at the packets class")

# 5. no service-side reference to a PE type may survive
service_text = (REPO / SERVICE).read_text(encoding="utf-8")
if "retrooper" in service_text:
    failed.append("service still mentions a retrooper type: "
                  + ", ".join(sorted({line.strip() for line in service_text.splitlines()
                                      if "retrooper" in line})))

print("applied (total) :", len(applied))
print("skipped (total) :", len(skipped))
if failed:
    for f in failed:
        print("   !", f)
    sys.exit(1)
