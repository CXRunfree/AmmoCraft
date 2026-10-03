package cn.crtlprototypestudios.ammocraft.registry;

import cn.crtlprototypestudios.ammocraft.AmmoCraft;
import cn.crtlprototypestudios.ammocraft.item.AmmoMoldItem;
import cn.crtlprototypestudios.ammocraft.item.AmmoCasingItem;
import cn.crtlprototypestudios.ammocraft.item.IncompleteAmmoItem;
import com.simibubi.create.AllTags;
import com.tterrag.registrate.util.entry.ItemEntry;
import net.minecraft.core.NonNullList;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.List;

public class AmmoItems {
    public static final ItemEntry<Item> BLANK_MOLD = AmmoCraft.REGISTRATE
            .item("blank_ammo_mold", Item::new)
            .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/blank_mold")))
            .lang("Blank Ammunition Mold")
            .register();

    public static final ItemEntry<Item> DISASSEMBLY_TOOL = item("ammo_disassembly_tool", "Ammunition Disassembly Pliers", true);
    public static final ItemEntry<Item> LAPIS_DUST = item("lapis_dust", "Lapis Dust", false);

    private static ItemEntry<Item> item(String id, String name, boolean single) {
        return AmmoCraft.REGISTRATE.item(id, Item::new)
                .properties(p -> single ? p.stacksTo(1) : p)
                .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/" + id)))
                .lang(name).register();
    }

    public static final List<Caliber> CALIBERS = List.of(
            // id, name, copper/iron/nuggets -> blanks, gunpowder/lapis dust/blaze powder -> doses
            new Caliber("9mm", "9mm", 2, 0, 0, 12, 1, 0, 0, 24),
            new Caliber("45acp", ".45 ACP", 4, 0, 0, 12, 2, 0, 0, 30),
            new Caliber("357mag", ".357 Magnum", 3, 0, 0, 6, 3, 0, 0, 24),
            new Caliber("50ae", ".50 AE", 5, 0, 0, 6, 5, 3, 0, 24),
            new Caliber("46x30", "4.6x30mm", 3, 0, 0, 12, 1, 0, 0, 24),
            new Caliber("57x28", "5.7x28mm", 4, 0, 0, 12, 1, 3, 0, 24),
            new Caliber("58x42", "5.8x42mm", 4, 0, 0, 12, 2, 0, 0, 24),
            new Caliber("68x51fury", "6.8x51mm FURY", 5, 0, 0, 12, 3, 0, 0, 24),
            new Caliber("556x45", "5.56x45mm", 4, 0, 0, 12, 2, 0, 0, 30),
            new Caliber("762x25", "7.62x25mm", 3, 0, 0, 12, 1, 0, 0, 24),
            new Caliber("762x39", "7.62x39mm", 5, 0, 0, 12, 2, 0, 0, 24),
            new Caliber("762x54", "7.62x54mm", 5, 0, 0, 12, 4, 0, 0, 30),
            new Caliber("308", ".308 Winchester", 6, 0, 0, 12, 4, 1, 0, 24),
            new Caliber("30_06", ".30-06 Springfield", 10, 0, 0, 12, 3, 0, 0, 12),
            new Caliber("338", ".338 Lapua Magnum", 9, 0, 0, 6, 5, 3, 0, 12),
            new Caliber("50bmg", ".50 BMG", 28, 0, 0, 6, 10, 6, 1, 12),
            new Caliber("12g", "12 Gauge", 10, 0, 0, 12, 4, 0, 0, 12),
            new Caliber("40mm", "40mm", 5, 2, 0, 3, 5, 0, 0, 3),
            new Caliber("rpg_rocket", "RPG Rocket", 30, 3, 0, 3, 12, 0, 0, 3)
    );

    public static void register() {
        // Invoking this method initializes the static item registrations.
    }

    public static void fillCreativeTab(NonNullList<ItemStack> items) {
        for (ItemEntry<Item> entry : List.of(BLANK_MOLD, DISASSEMBLY_TOOL, LAPIS_DUST))
            items.add(entry.get().getDefaultInstance());
        for (Caliber caliber : CALIBERS) {
            items.add(caliber.mold.get().getDefaultInstance());
            items.add(caliber.casing.get().getDefaultInstance());
            items.add(caliber.incomplete.get().getDefaultInstance());
            items.add(caliber.powder.get().getDefaultInstance());
        }
    }

    public static class Caliber {
        public final String id;
        public final ItemEntry<AmmoMoldItem> mold;
        public final ItemEntry<AmmoCasingItem> casing;
        public final ItemEntry<IncompleteAmmoItem> incomplete;
        public final ItemEntry<Item> powder;
        public final int copper, iron, ironNuggets, blanks, mixingDuration, powderMixingDuration;
        public final int gunpowder, lapis, blaze, doses;

        private Caliber(String id, String name, int copper, int iron, int ironNuggets, int blanks,
                        int gunpowder, int lapis, int blaze, int doses) {
            this.id = id;
            this.copper = copper;
            this.iron = iron;
            this.ironNuggets = ironNuggets;
            this.blanks = blanks;
            this.mixingDuration = switch (id) {
                case "9mm", "45acp", "46x30", "762x25" -> 64;
                case "357mag", "57x28", "58x42", "68x51fury", "556x45", "762x39" -> 96;
                case "50ae", "762x54", "308", "30_06", "12g" -> 128;
                case "338", "40mm" -> 192;
                case "50bmg", "rpg_rocket" -> 256;
                default -> throw new IllegalArgumentException("Unknown ammunition caliber: " + id);
            };
            this.powderMixingDuration = switch (id) {
                case "9mm", "45acp", "46x30", "762x25" -> 96;
                case "338", "40mm" -> 192;
                case "50bmg", "rpg_rocket" -> 256;
                default -> 128;
            };
            if (blanks < 1 || blanks > 12 || doses < 1 || doses > 30
                    || (id.equals("40mm") || id.equals("rpg_rocket")
                    ? blanks != 3 || doses != 3 : blanks % 6 != 0 || doses % 6 != 0))
                throw new IllegalArgumentException("Invalid ammunition batch: " + id);
            this.gunpowder = gunpowder;
            this.lapis = lapis;
            this.blaze = blaze;
            this.doses = doses;
            mold = AmmoCraft.REGISTRATE
                    .item("ammo_mold_" + id, p -> new AmmoMoldItem(p, id))
                    .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/ammo/molds/" + id)))
                    .lang(name + " Ammunition Mold")
                    .register();
            powder = AmmoCraft.REGISTRATE.item("ammo_powder_" + id, Item::new)
                    .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/ammo/powders/" + id)))
                    .lang(name + " Propellant").register();
            casing = AmmoCraft.REGISTRATE.item("casing_" + id, AmmoCasingItem::new)
                    .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/ammo/casings/" + id)))
                    .lang(name + " Casing")
                    .tag(AllTags.AllItemTags.UPRIGHT_ON_BELT.tag)
                    .register();
            incomplete = AmmoCraft.REGISTRATE
                    .item("incomplete_" + id, IncompleteAmmoItem::new)
                    .model((c, p) -> p.generated(c::getEntry, AmmoCraft.id("item/ammo/casings/" + id)))
                    .lang("Incomplete " + name + " Ammunition")
                    .tag(AllTags.AllItemTags.UPRIGHT_ON_BELT.tag)
                    .register();
        }
    }
}
