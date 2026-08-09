import re

# Load shop_prices_master.yml as raw text to preserve formatting, or rewrite clean
with open("shop_prices_master.yml", "r") as f:
    content = f.read()

# 1 Emerald = $3.00
# 1 Emerald Block = $27.00
# 1 Netherite Ingot = $192.00
# 1 Netherite Block = $1728.00

# Replace EMERALD and NETHERITE_INGOT entries in stone.yml / master
# We will create an explicit Currency Exchange section in EconomyShopGUI/sections/Building/stone.yml and master

with open("shop_prices_master.yml", "w") as f:
    f.write("""# ==============================================================================
#                  ALL ECONOMYSHOPGUI PRODUCTS & PRICES (VAULT $)
# ==============================================================================
# Master reference file for all products and Vault ($) prices in /shop.
# Formatted as YAML for easy viewing and manual edits.
# ==============================================================================

categories:
  old_currency_cash_in:
    category_name: "Old Currency Cash-In (Sell Only)"
    section_file: "EconomyShopGUI/sections/Building/stone.yml"
    items:
      - material: EMERALD
        buy: 0.00
        sell: 3.00
      - material: EMERALD_BLOCK
        buy: 0.00
        sell: 27.00
      - material: NETHERITE_INGOT
        buy: 0.00
        sell: 192.00
      - material: NETHERITE_BLOCK
        buy: 0.00
        sell: 1728.00
      - material: COBBLESTONE
        buy: 2.00
        sell: 0.50
      - material: STONE
        buy: 3.00
        sell: 1.00
      - material: SMOOTH_STONE
        buy: 4.00
        sell: 1.50
      - material: STONE_BRICKS
        buy: 4.00
        sell: 1.50
      - material: GRANITE
        buy: 3.00
        sell: 1.00
      - material: DIORITE
        buy: 3.00
        sell: 1.00
      - material: ANDESITE
        buy: 3.00
        sell: 1.00
      - material: DEEPSLATE
        buy: 3.50
        sell: 1.20
      - material: COBBLED_DEEPSLATE
        buy: 2.50
        sell: 0.80
      - material: COAL
        buy: 10.00
        sell: 4.00
      - material: RAW_IRON
        buy: 25.00
        sell: 10.00
      - material: IRON_INGOT
        buy: 30.00
        sell: 12.00
      - material: RAW_GOLD
        buy: 45.00
        sell: 18.00
      - material: GOLD_INGOT
        buy: 50.00
        sell: 20.00
      - material: DIAMOND
        buy: 500.00
        sell: 200.00
      - material: LAPIS_LAZULI
        buy: 15.00
        sell: 5.00
      - material: AMETHYST_SHARD
        buy: 40.00
        sell: 15.00
      - material: OBSIDIAN
        buy: 60.00
        sell: 25.00
      - material: ANCIENT_DEBRIS
        buy: 1500.00
        sell: 600.00
      - material: NETHERITE_SCRAP
        buy: 1800.00
        sell: 700.00

  wood_and_planks:
    category_name: "Woods & Planks"
    section_file: "EconomyShopGUI/sections/Building/wood.yml"
    items:
      - material: OAK_LOG
        buy: 5.00
        sell: 2.00
      - material: OAK_PLANKS
        buy: 1.25
        sell: 0.50
      - material: SPRUCE_LOG
        buy: 5.00
        sell: 2.00
      - material: SPRUCE_PLANKS
        buy: 1.25
        sell: 0.50
      - material: BIRCH_LOG
        buy: 5.00
        sell: 2.00
      - material: BIRCH_PLANKS
        buy: 1.25
        sell: 0.50
      - material: JUNGLE_LOG
        buy: 6.00
        sell: 2.50
      - material: ACACIA_LOG
        buy: 6.00
        sell: 2.50
      - material: DARK_OAK_LOG
        buy: 6.00
        sell: 2.50
      - material: MANGROVE_LOG
        buy: 7.00
        sell: 3.00
      - material: CHERRY_LOG
        buy: 8.00
        sell: 3.50
      - material: CRIMSON_STEM
        buy: 10.00
        sell: 4.00
      - material: WARPED_STEM
        buy: 10.00
        sell: 4.00

  natural_and_farming:
    category_name: "Natural & Farming"
    section_file: "EconomyShopGUI/sections/Building/natural.yml"
    items:
      - material: DIRT
        buy: 1.00
        sell: 0.20
      - material: GRASS_BLOCK
        buy: 5.00
        sell: 1.00
      - material: SAND
        buy: 2.00
        sell: 0.50
      - material: GRAVEL
        buy: 2.00
        sell: 0.50
      - material: CLAY
        buy: 6.00
        sell: 2.00
      - material: OAK_LEAVES
        buy: 2.00
        sell: 0.40
      - material: WHEAT
        buy: 5.00
        sell: 2.00
      - material: CARROT
        buy: 5.00
        sell: 2.00
      - material: POTATO
        buy: 5.00
        sell: 2.00
      - material: SUGAR_CANE
        buy: 8.00
        sell: 3.00
      - material: PUMPKIN
        buy: 10.00
        sell: 4.00
      - material: MELON_SLICE
        buy: 3.00
        sell: 1.00
      - material: NETHER_WART
        buy: 12.00
        sell: 5.00
      - material: GLOW_BERRIES
        buy: 10.00
        sell: 4.00

  decorative_and_glass:
    category_name: "Decorative & Glass"
    section_file: "EconomyShopGUI/sections/Building/decorative_blocks.yml"
    items:
      - material: GLASS
        buy: 4.00
        sell: 1.00
      - material: WHITE_WOOL
        buy: 6.00
        sell: 2.00
      - material: BLACK_WOOL
        buy: 6.00
        sell: 2.00
      - material: RED_WOOL
        buy: 6.00
        sell: 2.00
      - material: BLUE_WOOL
        buy: 6.00
        sell: 2.00
      - material: WHITE_CONCRETE
        buy: 8.00
        sell: 2.50
      - material: BLACK_CONCRETE
        buy: 8.00
        sell: 2.50
      - material: RED_CONCRETE
        buy: 8.00
        sell: 2.50
      - material: BLUE_CONCRETE
        buy: 8.00
        sell: 2.50
      - material: CYAN_CONCRETE
        buy: 8.00
        sell: 2.50
      - material: SEA_LANTERN
        buy: 50.00
        sell: 20.00
      - material: GLOWSTONE
        buy: 30.00
        sell: 10.00
      - material: SHULKER_BOX
        buy: 1200.00
        sell: 450.00

  weapons_and_armor:
    category_name: "Weapons & Armor"
    section_file: "EconomyShopGUI/sections/Combat/armor.yml"
    items:
      - material: IRON_SWORD
        buy: 100.00
        sell: 30.00
      - material: IRON_PICKAXE
        buy: 120.00
        sell: 40.00
      - material: IRON_CHESTPLATE
        buy: 300.00
        sell: 100.00
      - material: DIAMOND_SWORD
        buy: 1200.00
        sell: 450.00
      - material: DIAMOND_PICKAXE
        buy: 1600.00
        sell: 600.00
      - material: DIAMOND_CHESTPLATE
        buy: 4000.00
        sell: 1500.00
      - material: NETHERITE_SWORD
        buy: 9000.00
        sell: 3500.00
      - material: NETHERITE_CHESTPLATE
        buy: 12000.00
        sell: 4500.00
      - material: BOW
        buy: 80.00
        sell: 25.00
      - material: ARROW
        buy: 2.00
        sell: 0.50
      - material: SHIELD
        buy: 150.00
        sell: 50.00
      - material: TRIDENT
        buy: 8000.00
        sell: 3000.00

  redstone_and_mob_drops:
    category_name: "Redstone & Mob Drops"
    section_file: "EconomyShopGUI/sections/Combat/redstone.yml"
    items:
      - material: REDSTONE
        buy: 8.00
        sell: 3.00
      - material: REPEATER
        buy: 25.00
        sell: 8.00
      - material: COMPARATOR
        buy: 35.00
        sell: 12.00
      - material: PISTON
        buy: 45.00
        sell: 15.00
      - material: STICKY_PISTON
        buy: 60.00
        sell: 20.00
      - material: HOPPER
        buy: 200.00
        sell: 70.00
      - material: OBSERVER
        buy: 50.00
        sell: 18.00
      - material: DISPENSER
        buy: 40.00
        sell: 12.00
      - material: ROTTEN_FLESH
        buy: 3.00
        sell: 1.00
      - material: BONE
        buy: 4.00
        sell: 1.50
      - material: STRING
        buy: 5.00
        sell: 2.00
      - material: GUNPOWDER
        buy: 10.00
        sell: 4.00
      - material: SPIDER_EYE
        buy: 8.00
        sell: 3.00
      - material: ENDER_PEARL
        buy: 40.00
        sell: 15.00
      - material: BLAZE_ROD
        buy: 100.00
        sell: 40.00
      - material: SLIME_BALL
        buy: 20.00
        sell: 7.00
      - material: SHULKER_SHELL
        buy: 500.00
        sell: 200.00
      - material: NETHER_STAR
        buy: 5000.00
        sell: 2000.00
      - material: TOTEM_OF_UNDYING
        buy: 3000.00
        sell: 1200.00
""")

print("Updated shop_prices_master.yml with Sell-Only Old Currency Cash-In rates!")
