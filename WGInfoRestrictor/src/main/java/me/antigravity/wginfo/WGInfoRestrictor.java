package me.antigravity.wginfo;

import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerCommandPreprocessEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.Method;
import java.util.UUID;

public class WGInfoRestrictor extends JavaPlugin implements Listener {

    @Override
    public void onEnable() {
        getServer().getPluginManager().registerEvents(this, this);
        getLogger().info("WGInfoRestrictor reflection edition enabled successfully!");
    }

    @Override
    public void onDisable() {
        getLogger().info("WGInfoRestrictor disabled successfully!");
    }

    @EventHandler(priority = EventPriority.NORMAL)
    public void onCommandPreprocess(PlayerCommandPreprocessEvent event) {
        if (event.isCancelled()) return;

        Player player = event.getPlayer();
        String message = event.getMessage().trim();
        if (!message.startsWith("/")) return;

        String[] parts = message.substring(1).split("\\s+");
        if (parts.length == 0) return;

        // Block /rg flag commands for non-OP players
        if (isRegionFlagCommand(parts)) {
            if (!player.isOp()) {
                event.setCancelled(true);
                player.sendMessage("§cError: You do not have permission to modify region flags.");
                return;
            }
        }

        // Intercept /rg addowner, addmember, removeowner, removemember commands for non-OP players
        if (isRegionMemberCommand(parts)) {
            if (!player.isOp()) {
                event.setCancelled(true);
                handleRegionMemberReflection(player, parts);
                return;
            }
        }

        // Intercept /rg info commands for non-OP players
        if (isRegionInfoCommand(parts)) {
            if (!player.isOp()) {
                event.setCancelled(true);
                handleRegionInfoReflection(player, parts);
            }
        }
    }

    private boolean isRegionFlagCommand(String[] parts) {
        String base = parts[0].toLowerCase();
        if (base.equals("rg") || base.equals("region") || base.equals("wg") || 
            base.equals("worldguard:rg") || base.equals("worldguard:region")) {
            if (parts.length > 1 && parts[1].toLowerCase().equals("flag")) {
                return true;
            }
        }
        if (base.equals("worldguard")) {
            if (parts.length > 2 && parts[1].toLowerCase().equals("region") && parts[2].toLowerCase().equals("flag")) {
                return true;
            }
        }
        return false;
    }

    private boolean isRegionMemberCommand(String[] parts) {
        String base = parts[0].toLowerCase();
        String subCmd = "";
        if (base.equals("rg") || base.equals("region") || base.equals("wg") || 
            base.equals("worldguard:rg") || base.equals("worldguard:region")) {
            if (parts.length > 1) subCmd = parts[1].toLowerCase();
        } else if (base.equals("worldguard")) {
            if (parts.length > 2 && parts[1].toLowerCase().equals("region")) {
                subCmd = parts[2].toLowerCase();
            }
        }
        return subCmd.equals("addowner") || subCmd.equals("addmember") || 
               subCmd.equals("removeowner") || subCmd.equals("removemember");
    }

    private void handleRegionMemberReflection(Player player, String[] parts) {
        // Parse sub-command, region name, player name
        // Command syntax: /rg addmember <region> <player> OR /rg addmember -a <region> <player> etc.
        int startIndex = 1;
        if (parts[0].toLowerCase().equals("worldguard")) {
            startIndex = 3;
        } else {
            startIndex = 2;
        }

        String subCmd = "";
        if (parts[0].toLowerCase().equals("worldguard")) {
            subCmd = parts[2].toLowerCase();
        } else {
            subCmd = parts[1].toLowerCase();
        }

        String regionName = "";
        String targetPlayerName = "";

        if (parts.length > startIndex) {
            regionName = parts[startIndex];
        }
        if (parts.length > startIndex + 1) {
            targetPlayerName = parts[startIndex + 1];
        }

        if (regionName.isEmpty() || targetPlayerName.isEmpty()) {
            player.sendMessage("§cUsage: /rg " + subCmd + " <region> <player>");
            return;
        }

        try {
            Class<?> worldGuardClass = Class.forName("com.sk89q.worldguard.WorldGuard");
            Object wgInstance = worldGuardClass.getMethod("getInstance").invoke(null);
            Object platform = worldGuardClass.getMethod("getPlatform").invoke(wgInstance);
            Object container = platform.getClass().getMethod("getRegionContainer").invoke(platform);

            Class<?> bukkitAdapterClass = Class.forName("com.sk89q.worldedit.bukkit.BukkitAdapter");
            Object adaptedWorld = bukkitAdapterClass.getMethod("adapt", org.bukkit.World.class).invoke(null, player.getWorld());
            Object manager = container.getClass().getMethod("get", Class.forName("com.sk89q.worldedit.world.World")).invoke(container, adaptedWorld);

            if (manager == null) {
                player.sendMessage("§cWorldGuard region manager not found for this world.");
                return;
            }

            Object region = manager.getClass().getMethod("getRegion", String.class).invoke(manager, regionName);
            if (region == null) {
                player.sendMessage("§cRegion '" + regionName + "' not found.");
                return;
            }

            if (!isOwner(player, region)) {
                player.sendMessage("§cError: You can only manage members/owners of regions you own.");
                return;
            }

            Player targetPlayer = Bukkit.getPlayer(targetPlayerName);
            Object domain = null;
            if (subCmd.contains("owner")) {
                domain = region.getClass().getMethod("getOwners").invoke(region);
            } else {
                domain = region.getClass().getMethod("getMembers").invoke(region);
            }

            if (subCmd.startsWith("add")) {
                if (targetPlayer != null) {
                    domain.getClass().getMethod("addPlayer", UUID.class).invoke(domain, targetPlayer.getUniqueId());
                } else {
                    domain.getClass().getMethod("addPlayer", String.class).invoke(domain, targetPlayerName);
                }
                player.sendMessage("§aSuccessfully added §f" + targetPlayerName + " §ato region §f" + regionName + "§a!");
            } else if (subCmd.startsWith("remove")) {
                if (targetPlayer != null) {
                    domain.getClass().getMethod("removePlayer", UUID.class).invoke(domain, targetPlayer.getUniqueId());
                }
                domain.getClass().getMethod("removePlayer", String.class).invoke(domain, targetPlayerName);
                player.sendMessage("§aSuccessfully removed §f" + targetPlayerName + " §afrom region §f" + regionName + "§a!");
            }

            // Save region manager changes
            try {
                manager.getClass().getMethod("save").invoke(manager);
            } catch (Exception ignored) {}

        } catch (Exception e) {
            player.sendMessage("§cAn error occurred while executing region command.");
            getLogger().severe("Reflection error in WGInfoRestrictor member management: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private boolean isRegionInfoCommand(String[] parts) {
        String base = parts[0].toLowerCase();
        if (base.equals("rg") || base.equals("region") || base.equals("wg") || 
            base.equals("worldguard:rg") || base.equals("worldguard:region")) {
            if (parts.length > 1 && parts[1].toLowerCase().equals("info")) {
                return true;
            }
        }
        if (base.equals("worldguard")) {
            if (parts.length > 2 && parts[1].toLowerCase().equals("region") && parts[2].toLowerCase().equals("info")) {
                return true;
            }
        }
        return false;
    }

    private void handleRegionInfoReflection(Player player, String[] parts) {
        String regionName = "";
        if (parts[0].toLowerCase().equals("worldguard")) {
            if (parts.length > 3) {
                regionName = parts[3];
            }
        } else {
            if (parts.length > 2) {
                regionName = parts[2];
            }
        }

        try {
            // WorldGuard.getInstance()
            Class<?> worldGuardClass = Class.forName("com.sk89q.worldguard.WorldGuard");
            Object wgInstance = worldGuardClass.getMethod("getInstance").invoke(null);
            
            // wg.getPlatform().getRegionContainer()
            Object platform = worldGuardClass.getMethod("getPlatform").invoke(wgInstance);
            Object container = platform.getClass().getMethod("getRegionContainer").invoke(platform);

            Class<?> bukkitAdapterClass = Class.forName("com.sk89q.worldedit.bukkit.BukkitAdapter");

            if (!regionName.isEmpty()) {
                // container.get(BukkitAdapter.adapt(player.getWorld()))
                Object adaptedWorld = bukkitAdapterClass.getMethod("adapt", org.bukkit.World.class).invoke(null, player.getWorld());
                Object manager = container.getClass().getMethod("get", Class.forName("com.sk89q.worldedit.world.World")).invoke(container, adaptedWorld);

                if (manager == null) {
                    player.sendMessage("§cWorldGuard region manager not found for this world.");
                    return;
                }

                // manager.getRegion(regionName)
                Object region = manager.getClass().getMethod("getRegion", String.class).invoke(manager, regionName);
                if (region == null) {
                    player.sendMessage("§cRegion '" + regionName + "' not found.");
                    return;
                }

                if (isOwner(player, region)) {
                    sendCleanInfo(player, region);
                } else {
                    player.sendMessage("§cYou are not the owner of this region.");
                }
            } else {
                // container.createQuery()
                Object query = container.getClass().getMethod("createQuery").invoke(container);
                
                // BukkitAdapter.adapt(player.getLocation())
                Object adaptedLoc = bukkitAdapterClass.getMethod("adapt", org.bukkit.Location.class).invoke(null, player.getLocation());
                
                // query.getApplicableRegions(adaptedLoc)
                Object applicableRegions = query.getClass().getMethod("getApplicableRegions", Class.forName("com.sk89q.worldedit.util.Location")).invoke(query, adaptedLoc);
                
                Iterable<?> regionsIterable = (Iterable<?>) applicableRegions;
                Object ownedRegion = null;
                int count = 0;
                for (Object regionObj : regionsIterable) {
                    count++;
                    if (isOwner(player, regionObj)) {
                        ownedRegion = regionObj;
                        break;
                    }
                }

                if (ownedRegion != null) {
                    sendCleanInfo(player, ownedRegion);
                } else {
                    if (count == 0) {
                        player.sendMessage("§cYou are not standing in any region.");
                    } else {
                        player.sendMessage("§cYou do not own any region at this location.");
                    }
                }
            }
        } catch (Exception e) {
            player.sendMessage("§cAn error occurred while retrieving region info.");
            getLogger().severe("Reflection error in WGInfoRestrictor: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private boolean isOwner(Player player, Object regionObj) throws Exception {
        Object owners = regionObj.getClass().getMethod("getOwners").invoke(regionObj);
        Method containsUUID = owners.getClass().getMethod("contains", UUID.class);
        Method containsName = owners.getClass().getMethod("contains", String.class);
        
        boolean hasUUID = (boolean) containsUUID.invoke(owners, player.getUniqueId());
        boolean hasName = (boolean) containsName.invoke(owners, player.getName());
        return hasUUID || hasName;
    }

    private void sendCleanInfo(Player player, Object regionObj) throws Exception {
        String id = (String) regionObj.getClass().getMethod("getId").invoke(regionObj);
        String type = regionObj.getClass().getMethod("getType").invoke(regionObj).toString();
        int priority = (int) regionObj.getClass().getMethod("getPriority").invoke(regionObj);
        
        Object minPoint = regionObj.getClass().getMethod("getMinimumPoint").invoke(regionObj);
        Object maxPoint = regionObj.getClass().getMethod("getMaximumPoint").invoke(regionObj);
        String bounds = minPoint.toString() + " to " + maxPoint.toString();
        
        Object owners = regionObj.getClass().getMethod("getOwners").invoke(regionObj);
        Object members = regionObj.getClass().getMethod("getMembers").invoke(regionObj);
        
        String ownersStr = formatDomain(owners);
        String membersStr = formatDomain(members);

        player.sendMessage("§9=========================================");
        player.sendMessage("§bRegion: §f" + id);
        player.sendMessage("§bType: §f" + type + " §7(Priority: " + priority + ")");
        player.sendMessage("§bBounds: §f" + bounds);
        player.sendMessage("§bOwners: §f" + (ownersStr.isEmpty() ? "(none)" : ownersStr));
        player.sendMessage("§bMembers: §f" + (membersStr.isEmpty() ? "(none)" : membersStr));
        player.sendMessage("§7-----------------------------------------");
        player.sendMessage("§e§lRegion Actions Menu:");
        
        try {
            net.md_5.bungee.api.chat.TextComponent addMemberBtn = new net.md_5.bungee.api.chat.TextComponent(" §a[+ Add Member] ");
            addMemberBtn.setClickEvent(new net.md_5.bungee.api.chat.ClickEvent(net.md_5.bungee.api.chat.ClickEvent.Action.SUGGEST_COMMAND, "/rg addmember " + id + " "));
            addMemberBtn.setHoverEvent(new net.md_5.bungee.api.chat.HoverEvent(net.md_5.bungee.api.chat.HoverEvent.Action.SHOW_TEXT, new net.md_5.bungee.api.chat.ComponentBuilder("§7Click to suggest: §f/rg addmember " + id + " <player>").create()));

            net.md_5.bungee.api.chat.TextComponent removeMemberBtn = new net.md_5.bungee.api.chat.TextComponent(" §c[- Remove Member] ");
            removeMemberBtn.setClickEvent(new net.md_5.bungee.api.chat.ClickEvent(net.md_5.bungee.api.chat.ClickEvent.Action.SUGGEST_COMMAND, "/rg removemember " + id + " "));
            removeMemberBtn.setHoverEvent(new net.md_5.bungee.api.chat.HoverEvent(net.md_5.bungee.api.chat.HoverEvent.Action.SHOW_TEXT, new net.md_5.bungee.api.chat.ComponentBuilder("§7Click to suggest: §f/rg removemember " + id + " <player>").create()));

            net.md_5.bungee.api.chat.TextComponent addOwnerBtn = new net.md_5.bungee.api.chat.TextComponent(" §a[+ Add Owner] ");
            addOwnerBtn.setClickEvent(new net.md_5.bungee.api.chat.ClickEvent(net.md_5.bungee.api.chat.ClickEvent.Action.SUGGEST_COMMAND, "/rg addowner " + id + " "));
            addOwnerBtn.setHoverEvent(new net.md_5.bungee.api.chat.HoverEvent(net.md_5.bungee.api.chat.HoverEvent.Action.SHOW_TEXT, new net.md_5.bungee.api.chat.ComponentBuilder("§7Click to suggest: §f/rg addowner " + id + " <player>").create()));

            net.md_5.bungee.api.chat.TextComponent removeOwnerBtn = new net.md_5.bungee.api.chat.TextComponent(" §c[- Remove Owner]");
            removeOwnerBtn.setClickEvent(new net.md_5.bungee.api.chat.ClickEvent(net.md_5.bungee.api.chat.ClickEvent.Action.SUGGEST_COMMAND, "/rg removeowner " + id + " "));
            removeOwnerBtn.setHoverEvent(new net.md_5.bungee.api.chat.HoverEvent(net.md_5.bungee.api.chat.HoverEvent.Action.SHOW_TEXT, new net.md_5.bungee.api.chat.ComponentBuilder("§7Click to suggest: §f/rg removeowner " + id + " <player>").create()));

            net.md_5.bungee.api.chat.TextComponent memberLine = new net.md_5.bungee.api.chat.TextComponent("§bMembers: ");
            memberLine.addExtra(addMemberBtn);
            memberLine.addExtra(removeMemberBtn);

            net.md_5.bungee.api.chat.TextComponent ownerLine = new net.md_5.bungee.api.chat.TextComponent("§bOwners: ");
            ownerLine.addExtra(addOwnerBtn);
            ownerLine.addExtra(removeOwnerBtn);

            player.spigot().sendMessage(ownerLine);
            player.spigot().sendMessage(memberLine);
        } catch (Throwable t) {
            player.sendMessage(" §bOwners: §a/rg addowner " + id + " <player> §7| §c/rg removeowner " + id + " <player>");
            player.sendMessage(" §bMembers: §a/rg addmember " + id + " <player> §7| §c/rg removemember " + id + " <player>");
        }

        player.sendMessage("§9=========================================");
    }

    private String formatDomain(Object domainObj) {
        if (domainObj == null) return "(none)";
        try {
            java.util.Set<?> playersSet = (java.util.Set<?>) domainObj.getClass().getMethod("getPlayers").invoke(domainObj);
            java.util.List<String> names = new java.util.ArrayList<>();

            if (playersSet != null) {
                for (Object pObj : playersSet) {
                    if (pObj == null) continue;
                    String pStr = pObj.toString();
                    
                    // Check if it's a UUID string
                    try {
                        UUID uuid = UUID.fromString(pStr);
                        names.add(getPlayerNameFromUUID(uuid));
                    } catch (IllegalArgumentException e) {
                        // It's already a plain player username string
                        names.add(pStr);
                    }
                }
            }

            // Also check getUniqueIds() directly if available
            try {
                java.util.Set<UUID> uniqueIds = (java.util.Set<UUID>) domainObj.getClass().getMethod("getUniqueIds").invoke(domainObj);
                if (uniqueIds != null) {
                    for (UUID uuid : uniqueIds) {
                        String resolved = getPlayerNameFromUUID(uuid);
                        if (!names.contains(resolved)) {
                            names.add(resolved);
                        }
                    }
                }
            } catch (Exception ignored) {}

            return names.isEmpty() ? "(none)" : String.join(", ", names);
        } catch (Exception e) {
            try {
                String fallback = (String) domainObj.getClass().getMethod("toPlayersString").invoke(domainObj);
                return (fallback == null || fallback.isEmpty()) ? "(none)" : fallback;
            } catch (Exception ex) {
                return "(none)";
            }
        }
    }

    private String getPlayerNameFromUUID(UUID uuid) {
        if (uuid == null) return "Unknown";
        
        // 1. Check online players
        org.bukkit.entity.Player online = Bukkit.getPlayer(uuid);
        if (online != null && online.getName() != null) {
            return online.getName();
        }

        // 2. Check offline player cache
        org.bukkit.OfflinePlayer offline = Bukkit.getOfflinePlayer(uuid);
        if (offline != null && offline.getName() != null) {
            return offline.getName();
        }

        // 3. Complete fallback map for server UUIDs (Geyser/Bedrock + Java offline mode)
        String uuidStr = uuid.toString().toLowerCase();
        if (uuidStr.equals("95204d3f-ea6c-3dfa-929d-9180927184f8")) return "manansaleh2007";
        if (uuidStr.equals("d413c28e-64bb-32af-9661-3e901bc6e22b")) return "NightmareDady";
        if (uuidStr.equals("2d5bf9b3-5a85-3026-a136-4680097f11f1")) return "azansalehhh";
        if (uuidStr.equals("a016f4ef-5e76-32d7-b895-bb0498b8bd2a")) return "azansalehhh";
        if (uuidStr.equals("00000000-0000-0000-0009-01f4482c7d17")) return ".HastyBag7675";
        if (uuidStr.equals("00000000-0000-0000-0009-01f2533ef34a")) return ".WiryCircle3938";
        if (uuidStr.equals("00000000-0000-0000-0009-01f114c00043")) return ".mustafahacker67";
        if (uuidStr.equals("00000000-0000-0000-0009-01f9433f6353")) return ".mustafahacker67";

        return uuid.toString();
    }
}
