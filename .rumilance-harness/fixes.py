#!/usr/bin/env python3
"""Re-apply the RumilancePractice fixes (idempotent).

Usage: python3 fixes.py [repo-root]        (default /home/user/RumilancePractice)

Every patch skips itself when the applied form is already present and fails loudly when the
anchor text has drifted, so a partially-applied tree is safe to re-run.
"""
import pathlib
import sys

REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path("/home/user/RumilancePractice")

applied = []
skipped = []
failed = []


def patch(rel, old, new, label, marker=None):
    """Replace `old` with `new`. `marker` must be a snippet that only the applied form has."""
    path = REPO / rel
    text = path.read_text(encoding="utf-8")
    # Two patch shapes need opposite "already applied" tests. When the replacement contains the
    # anchor (an insertion), the applied form still contains the anchor, so presence of `new` is
    # the test. When it does not (a rename/removal), a missing anchor is the test - and for
    # removals `new` is often a snippet that exists in the untouched file, which is how an
    # import block survived a naive check.
    already = (new in text) if (old in new) else (old not in text)
    if already and (marker is None or marker in text):
        skipped.append(label)
        return
    if text.count(old) != 1:
        failed.append(f"{label}: anchor x{text.count(old)}, want 1")
        return
    path.write_text(text.replace(old, new), encoding="utf-8")
    applied.append(label)


# ---------------------------------------------------------------------------
# 1. The duel message reported a kit argument that does not exist (#4):
#    /duel <player> with no kit defaults to the first kit, then the not-found message read
#    args[1] - an ArrayIndexOutOfBounds waiting to happen, and the wrong name when it did not.
patch("src/main/java/com/rumilance/practice/command/DuelCommand.java",
      """                if (kitService.get(kit).filter(k -> k.enabled()).isEmpty()) {
                    messageService.send(player, "kit.not-found", MessageService.tags("kit", args[1]));""",
      """                if (kitService.get(kit).filter(k -> k.enabled()).isEmpty()) {
                    // args[1] does not exist when the kit was defaulted - report the default.
                    messageService.send(player, "kit.not-found", MessageService.tags("kit", kit));""",
      "duel: the not-found message reports the kit it actually checked",
      marker="report the default")

# ---------------------------------------------------------------------------
# 2. A setter annotated as an event handler (#13). Paper treats @EventHandler methods as
#    listeners, so the DI setter was registered as a handler for PlayerJoinEvent and the real
#    onJoin handler carried no annotation at all - every join-time bootstrap was silently dead.
patch("src/main/java/com/rumilance/practice/listener/SessionBootstrapListener.java",
      """    @EventHandler(priority = EventPriority.LOWEST)
    public void setBlockListService(
            com.rumilance.practice.social.BlockListService blockListService) {
        this.blockListService = blockListService;
    }

    public void onJoin(PlayerJoinEvent event) {""",
      """    public void setBlockListService(
            com.rumilance.practice.social.BlockListService blockListService) {
        this.blockListService = blockListService;
    }

    @EventHandler(priority = EventPriority.LOWEST)
    public void onJoin(PlayerJoinEvent event) {""",
      "join bootstrap: the @EventHandler annotation moved off the setter onto onJoin",
      marker="public void onJoin(PlayerJoinEvent event) {")

# ---------------------------------------------------------------------------
# 3. Combat-style reset was not scoped to its match (#14). resetMatch() reset EVERY player in
#    appliedModes and then cleared the map, so ending match A reverted the attack speed of
#    players still fighting in match B (BEDROCK's 16.0 silently back to Java's 4.0) and threw
#    away their bookkeeping. The record below tags each applied mode with its match.
patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """    /** playerId → CombatMode applied at match start (for reset). */
    private final Map<UUID, CombatMode> appliedModes = new ConcurrentHashMap<>();""",
      """    /** playerId → combat mode applied at match start, tagged with the match that applied it. */
    private final Map<UUID, Applied> appliedModes = new ConcurrentHashMap<>();

    /** One player's applied combat mode: which match owns it, and what it is. */
    private record Applied(String matchId, CombatMode mode) { }""",
      "combat style: applied modes remember their match",
      marker="private record Applied(")

patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """            CombatMode mode = global != null ? global
                    : CombatMode.defaultFor(PlayerPlatform.of(p));
            applyToPlayer(p, mode);""",
      """            CombatMode mode = global != null ? global
                    : CombatMode.defaultFor(PlayerPlatform.of(p));
            applyToPlayer(p, mode);
            appliedModes.put(uid, new Applied(matchId, mode));""",
      "combat style: applyToMatch records the match id with the mode",
      marker="new Applied(matchId, mode)")

patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """    /**
     * マッチ終了: 全員をデフォルト攻撃速度に戻し、モード記録を消去。
     */
    public void resetMatch(String matchId) {""",
      """    /**
     * マッチ終了: <b>このマッチの</b>参加者をデフォルト攻撃速度に戻し、モード記録を消去。
     * 他のマッチで戦っているプレイヤーには触れない。
     */
    public void resetMatch(String matchId) {""",
      "combat style: resetMatch javadoc says it is match-scoped",
      marker="このマッチの</b>")

patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """    public void resetMatch(String matchId) {
        matchModes.remove(matchId);
        // appliedModes からこの match に属していたプレイヤーをリセット
        for (Map.Entry<UUID, CombatMode> e : appliedModes.entrySet()) {
            Player p = Bukkit.getPlayer(e.getKey());
            if (p != null && p.isOnline()) {
                resetPlayer(p);
            }
        }
        appliedModes.clear();
    }""",
      """    public void resetMatch(String matchId) {
        matchModes.remove(matchId);
        // Only the players THIS match applied to: the loop used to reset everyone in the map and
        // then clear it, which reverted players who were mid-fight in another match.
        for (Map.Entry<UUID, Applied> e : appliedModes.entrySet()) {
            if (!matchId.equals(e.getValue().matchId())) {
                continue;
            }
            Player p = Bukkit.getPlayer(e.getKey());
            if (p != null && p.isOnline()) {
                resetPlayer(p);
            } else {
                appliedModes.remove(e.getKey(), e.getValue());
            }
        }
    }""",
      "combat style: resetMatch only touches its own match",
      marker="Only the players THIS match applied to")

patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """        attr.getModifiers().forEach(attr::removeModifier);
        attr.setBaseValue(target);
        appliedModes.put(player.getUniqueId(), mode);
    }""",
      """        attr.getModifiers().forEach(attr::removeModifier);
        attr.setBaseValue(target);
    }""",
      "combat style: applyToPlayer no longer records a match-less mode",
      marker="attr.setBaseValue(target);\n    }")

patch("src/main/java/com/rumilance/practice/combat/CombatStyleService.java",
      """    public CombatMode getAppliedMode(UUID playerId) {
        return appliedModes.get(playerId);
    }""",
      """    public CombatMode getAppliedMode(UUID playerId) {
        Applied applied = appliedModes.get(playerId);
        return applied == null ? null : applied.mode();
    }""",
      "combat style: getAppliedMode reads through the record",
      marker="return applied == null ? null : applied.mode();")

# ---------------------------------------------------------------------------
# 4. The ledge drill handed out slow falling with INFINITE_DURATION and nothing ever took it
#    back (#15): leaving the drill room, switching to a normal fight or quitting to the lobby
#    all kept the player floating. The drill now saves what was there and restores it.
patch("src/main/java/com/rumilance/practice/practice/PracticeSession.java",
      """    private org.bukkit.inventory.ItemStack drillSavedChest;
    private boolean drillElytraDressed;""",
      """    private org.bukkit.inventory.ItemStack drillSavedChest;
    private boolean drillElytraDressed;
    /**
     * Player's slow-falling effect swapped away by the ledge drill, or {@code null} if the drill
     * added it from nothing (restored/removed on teardown).
     */
    private org.bukkit.potion.PotionEffect drillSavedSlowFalling;
    private boolean drillSlowFallingDressed;""",
      "drill: the session remembers the player's own slow falling",
      marker="drillSavedSlowFalling;")

patch("src/main/java/com/rumilance/practice/practice/PracticeSession.java",
      """    public boolean drillElytraDressed() {
        return drillElytraDressed;
    }""",
      """    public boolean drillElytraDressed() {
        return drillElytraDressed;
    }

    public org.bukkit.potion.PotionEffect drillSavedSlowFalling() {
        return drillSavedSlowFalling;
    }

    public void setDrillSavedSlowFalling(org.bukkit.potion.PotionEffect effect) {
        this.drillSavedSlowFalling = effect;
    }

    public boolean drillSlowFallingDressed() {
        return drillSlowFallingDressed;
    }

    public void setDrillSlowFallingDressed(boolean dressed) {
        this.drillSlowFallingDressed = dressed;
    }""",
      "drill: slow-falling accessors on the session",
      marker="public org.bukkit.potion.PotionEffect drillSavedSlowFalling()")

patch("src/main/java/com/rumilance/practice/practice/PracticeService.java",
      """            case CRYSTAL_LEDGE ->
                player.addPotionEffect(new org.bukkit.potion.PotionEffect(
                        org.bukkit.potion.PotionEffectType.SLOW_FALLING,
                        org.bukkit.potion.PotionEffect.INFINITE_DURATION, 0, false, false, true));
            default -> { }
        }
    }""",
      """            case CRYSTAL_LEDGE -> {
                dressSlowFalling(player, session);
                player.addPotionEffect(new org.bukkit.potion.PotionEffect(
                        org.bukkit.potion.PotionEffectType.SLOW_FALLING,
                        org.bukkit.potion.PotionEffect.INFINITE_DURATION, 0, false, false, true));
            }
            default -> { }
        }
    }

    /**
     * Gives the player the ledge drill's slow falling, remembering whatever they had before so
     * teardown can put it back.
     */
    private void dressSlowFalling(Player player, PracticeSession session) {
        if (session.drillSlowFallingDressed()) {
            return;
        }
        session.setDrillSavedSlowFalling(
                player.getPotionEffect(org.bukkit.potion.PotionEffectType.SLOW_FALLING));
        session.setDrillSlowFallingDressed(true);
    }""",
      "drill: the ledge grants slow falling through a save/restore helper",
      marker="private void dressSlowFalling(")

patch("src/main/java/com/rumilance/practice/practice/PracticeService.java",
      """            session.setDrillElytraDressed(false);
            session.setDrillSavedChest(null);
        }
    }""",
      """            session.setDrillElytraDressed(false);
            session.setDrillSavedChest(null);
        }
        if (session != null && session.drillSlowFallingDressed()) {
            // The drill hands out slow falling with INFINITE_DURATION - without this the player
            // never falls again: leaving the room, switching to a normal fight or quitting to the
            // lobby all kept it, and the effect even survived into later matches.
            player.removePotionEffect(org.bukkit.potion.PotionEffectType.SLOW_FALLING);
            org.bukkit.potion.PotionEffect before = session.drillSavedSlowFalling();
            if (before != null) {
                player.addPotionEffect(before);
            }
            session.setDrillSlowFallingDressed(false);
            session.setDrillSavedSlowFalling(null);
        }
    }""",
      "drill: teardown removes/restores the drill's slow falling",
      marker="the player\n            // never falls again")

patch("src/main/java/com/rumilance/practice/practice/PracticeService.java",
      """                if (!player.hasPotionEffect(org.bukkit.potion.PotionEffectType.SLOW_FALLING)) {
                    player.addPotionEffect(new org.bukkit.potion.PotionEffect(
                            org.bukkit.potion.PotionEffectType.SLOW_FALLING, 20 * 30, 0,
                            false, false, true));
                }""",
      """                if (!player.hasPotionEffect(org.bukkit.potion.PotionEffectType.SLOW_FALLING)) {
                    dressSlowFalling(player, session);
                    player.addPotionEffect(new org.bukkit.potion.PotionEffect(
                            org.bukkit.potion.PotionEffectType.SLOW_FALLING, 20 * 30, 0,
                            false, false, true));
                }""",
      "drill: the mid-run ledge refresh also records the save",
      marker="dressSlowFalling(player, session);\n                    player.addPotionEffect")

# ---------------------------------------------------------------------------
# 5. TrimAllowanceService wrote its data file straight into the plugin data folder while the
#    rest of the plugin uses PluginIdentity#dataFile (shared folder naming) - the allowance
#    silently lived in a different place from every other file.
patch("src/main/java/com/rumilance/practice/cosmetic/TrimAllowanceService.java",
      """        this.file = new File(plugin.getDataFolder(), "trim-allowance.yml");""",
      """        this.file = com.rumilance.practice.PluginIdentity.dataFile(plugin, "trim-allowance.yml");""",
      "trim allowance: writes through PluginIdentity like every other file",
      marker="PluginIdentity.dataFile(plugin, \"trim-allowance.yml\")")

# ---------------------------------------------------------------------------
# 6. The bot-fight harness looked its fake players up by the LABEL given on the command line,
#    but a fake player's Bukkit name is generated (NARENA_BOT_xxxxx), so every lookup returned
#    null: the fight never started, the gamemode reset never ran, and status/stop skipped them.
patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """    private void startRound(PracticeType type, BotDifficulty difficulty, int seconds, String roomId,
                            String dummyName, int[] left, CommandSender sender) {
        Player player = Bukkit.getPlayerExact(dummyName);""",
      """    /**
     * The Player behind a dummy label. A fake player is registered under a generated profile
     * name (NARENA_BOT_xxxxx), so {@code Bukkit.getPlayerExact(label)} never matched and every
     * branch guarded by it was dead code: the rounds reported "dummy offline" and never started,
     * and the gamemode reset after spawning never ran (leaving the dummy in the server's default
     * game mode, where it cannot be hurt at all).
     */
    private Player dummyPlayer(String label) {
        PacketBotBody body = dummies.get(label);
        if (body == null) {
            return null;
        }
        try {
            Player player = (Player) body.bot().getBukkitEntity();
            return player != null && player.isOnline() ? player : null;
        } catch (Throwable ignored) {
            // Removed entity / shutdown race: treat the dummy as offline.
            return null;
        }
    }

    private void startRound(PracticeType type, BotDifficulty difficulty, int seconds, String roomId,
                            String dummyName, int[] left, CommandSender sender) {
        Player player = dummyPlayer(dummyName);""",
      "harness: dummies resolve through the spawned body, not the label")

patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """        dummies.put(name, body);
        Player player = Bukkit.getPlayerExact(name);""",
      """        dummies.put(name, body);
        Player player = dummyPlayer(name);""",
      "harness: the spawn command resolves the new dummy through the body")

patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """        for (String name : dummies.keySet()) {
            Player player = Bukkit.getPlayerExact(name);
            if (player == null) {
                continue;
            }""",
      """        for (String name : dummies.keySet()) {
            Player player = dummyPlayer(name);
            if (player == null) {
                continue;
            }""",
      "harness: end() resolves dummies through the body")

patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """            for (String name : List.copyOf(dummies.keySet())) {
                Player player = Bukkit.getPlayerExact(name);""",
      """            for (String name : List.copyOf(dummies.keySet())) {
                Player player = dummyPlayer(name);""",
      "harness: the keep-alive task resolves dummies through the body")

patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """        for (String name : dummies.keySet()) {
            Player player = Bukkit.getPlayerExact(name);
            out.append(" [").append(name).append(player == null ? " offline" : " online hp=\"""",
      """        for (String name : dummies.keySet()) {
            Player player = dummyPlayer(name);
            out.append(" [").append(name).append(player == null ? " offline" : " online hp=\"""",
      "harness: status resolves dummies through the body")

patch("src/main/java/com/rumilance/practice/practice/BotFightHarness.java",
      """        for (String name : names) {
            Player player = Bukkit.getPlayerExact(name);
            if (player != null) {""",
      """        for (String name : names) {
            Player player = dummyPlayer(name);
            if (player != null) {""",
      "harness: stop resolves dummies through the body")

# ---------------------------------------------------------------------------
# 7. The recent-opponent block never expired (#18). Nothing removed these entries, so one match
#    permanently blocked that pair (a player who logged out for the night came back still unable
#    to meet their last opponent) and the map grew one entry per player ever matched, forever.
patch("src/main/java/com/rumilance/practice/queue/QueueService.java",
      """    /** Remove entries for players who are no longer connected. */
    public synchronized void pruneOffline() {
        byPlayer.values().removeIf(entries -> {
            entries.removeIf(entry -> org.bukkit.Bukkit.getPlayer(entry.playerId()) == null);
            return entries.isEmpty();
        });
        for (List<QueueEntry> list : byQueue.values()) {
            list.removeIf(e -> org.bukkit.Bukkit.getPlayer(e.playerId()) == null);
        }
    }""",
      """    /** Remove entries for players who are no longer connected. */
    public synchronized void pruneOffline() {
        byPlayer.values().removeIf(entries -> {
            entries.removeIf(entry -> org.bukkit.Bukkit.getPlayer(entry.playerId()) == null);
            return entries.isEmpty();
        });
        for (List<QueueEntry> list : byQueue.values()) {
            list.removeIf(e -> org.bukkit.Bukkit.getPlayer(e.playerId()) == null);
        }
        // The recent-opponent block only means anything while BOTH fighters are still online: it
        // stops an instant rematch against the person you just fought. Nothing ever removed these
        // entries, so one match permanently blocked that pair (a player who logged out for the
        // night came back still unable to meet their last opponent) and the map grew one entry per
        // player ever matched, forever.
        recentOpponents.entrySet().removeIf(e ->
                org.bukkit.Bukkit.getPlayer(e.getKey()) == null
                        || org.bukkit.Bukkit.getPlayer(e.getValue()) == null);
    }""",
      "queue: expire the recent-opponent block with the session",
      marker="recentOpponents.entrySet().removeIf(")

# ---------------------------------------------------------------------------
# 8. The anti-stall counter never reset (#19): the count sat at 3+ forever, so every later
#    forced draw re-banned the player without them earning three new stall reports first - and
#    strikes from months ago still counted towards the next ban.
patch("src/main/java/com/rumilance/practice/match/MatchService.java",
      """    /** Count of matches that hit the absolute 1-hour hard limit (per player). 3 = 4-day ban. */
    private final Map<UUID, Integer> hardTimeoutStrikes = new ConcurrentHashMap<>();""",
      """    /**
     * Forced 1-hour draws per player, with the time of the last one. 3 inside
     * {@link #HARD_TIMEOUT_STRIKE_WINDOW_MS} = 4-day ban; the count starts over once the window
     * has passed, or the moment the ban is issued.
     */
    private final Map<UUID, HardTimeoutStrike> hardTimeoutStrikes = new ConcurrentHashMap<>();

    /** One player's forced draws: {@code count} falls back to 1 when the last one is too old. */
    private record HardTimeoutStrike(int count, long lastAtMs) { }""",
      "match: strikes carry their timestamp",
      marker="private record HardTimeoutStrike(")

patch("src/main/java/com/rumilance/practice/match/MatchService.java",
      """    private static final int HARD_TIMEOUT_STRIKES_BAN = 3;""",
      """    private static final int HARD_TIMEOUT_STRIKES_BAN = 3;
    /** Older forced draws are forgotten: the ban is for stalling, not for ancient history. */
    private static final long HARD_TIMEOUT_STRIKE_WINDOW_MS = 7L * 24 * 60 * 60 * 1000;""",
      "match: 7-day strike window",
      marker="HARD_TIMEOUT_STRIKE_WINDOW_MS = 7L")

patch("src/main/java/com/rumilance/practice/match/MatchService.java",
      """                    int strikes = hardTimeoutStrikes.merge(id, 1, Integer::sum);
                    if (strikes >= HARD_TIMEOUT_STRIKES_BAN && chatBanService != null) {""",
      """                    long nowMs = System.currentTimeMillis();
                    HardTimeoutStrike previous = hardTimeoutStrikes.get(id);
                    int strikes = previous == null
                            || nowMs - previous.lastAtMs() > HARD_TIMEOUT_STRIKE_WINDOW_MS
                            ? 1
                            : previous.count() + 1;
                    // Starting a fresh window on the third strike: the count used to sit at 3+
                    // forever, so every later forced draw re-banned the player without them
                    // earning three new stall reports first.
                    hardTimeoutStrikes.put(id, new HardTimeoutStrike(
                            strikes >= HARD_TIMEOUT_STRIKES_BAN ? 0 : strikes, nowMs));
                    if (strikes >= HARD_TIMEOUT_STRIKES_BAN && chatBanService != null) {""",
      "match: count strikes inside a window and reset after the ban",
      marker="HardTimeoutStrike previous = hardTimeoutStrikes.get(id);")

# ---------------------------------------------------------------------------
# 9. The attack-speed attribute was only ever reset by CombatStyleService. A player who leaves a
#    match early, or a server that restarts mid-match, skipped that reset - and vanilla persists
#    attribute base values in the player file, so a Bedrock match (16.0 = no attack cooldown)
#    could stick until some later match overwrote it. The lobby return is the out-of-combat
#    authority, so it undoes it there.
patch("src/main/java/com/rumilance/practice/util/PlayerVitals.java",
      """    /** Reset a team-config body-size SCALE attribute back to the vanilla 1.0. */""",
      """    /**
     * Reset the ATTACK_SPEED attribute to the Java default (4.0) and drop any modifiers.
     *
     * <p>Attack speed is the one combat attribute the lobby has to undo by hand: matches may set
     * it to the Bedrock value (16.0, see {@code CombatStyleService}) and a player who leaves a
     * match early - or a server that restarts mid-match - skips that service's own reset. Vanilla
     * persists attribute base values in the player's file, so without this the player keeps the
     * no-cooldown attack speed across a restart until some later match overwrites it.</p>
     */
    public static void resetAttackSpeed(Player player) {
        if (player == null) {
            return;
        }
        try {
            org.bukkit.attribute.AttributeInstance speedAttr =
                    player.getAttribute(org.bukkit.attribute.Attribute.ATTACK_SPEED);
            if (speedAttr != null) {
                // Mirrors CombatStyleService.resetPlayer: attack speed belongs to the combat
                // system, so every modifier on it is ours to remove.
                speedAttr.getModifiers().forEach(speedAttr::removeModifier);
                speedAttr.setBaseValue(4.0d);
            }
        } catch (RuntimeException | NoSuchFieldError | NoClassDefFoundError ignored) {
            // Older/newer servers without the attribute: nothing to reset.
        }
    }

    /** Reset a team-config body-size SCALE attribute back to the vanilla 1.0. */""",
      "vitals: resetAttackSpeed helper")

patch("src/main/java/com/rumilance/practice/lobby/LobbyService.java",
      """        com.rumilance.practice.util.PlayerVitals.clearCombatState(player);
        com.rumilance.practice.util.PlayerVitals.resetMaxHealth(player);""",
      """        com.rumilance.practice.util.PlayerVitals.clearCombatState(player);
        com.rumilance.practice.util.PlayerVitals.resetMaxHealth(player);
        // Attack speed is not a potion effect, so clearCombatState cannot see it: a match may have
        // set the Bedrock value (16.0) and every path that skips CombatStyleService.resetMatch -
        // leaving a match early, a restart mid-match - would keep it, permanently once saved.
        com.rumilance.practice.util.PlayerVitals.resetAttackSpeed(player);""",
      "lobby: the hub return undoes the match's attack speed")

print("applied  :", applied)
print("skipped  :", skipped or "-")
if failed:
    for f in failed:
        print("   !", f)
    sys.exit(1)
