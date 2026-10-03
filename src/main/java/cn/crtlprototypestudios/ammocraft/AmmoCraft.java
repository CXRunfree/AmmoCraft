package cn.crtlprototypestudios.ammocraft;

import cn.crtlprototypestudios.ammocraft.registry.AmmoItems;
import cn.crtlprototypestudios.ammocraft.registry.AmmoRecipes;
import com.simibubi.create.foundation.data.CreateRegistrate;
import net.minecraft.core.NonNullList;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(AmmoCraft.MOD_ID)
public class AmmoCraft {
    public static final String MOD_ID = "ammocraft";
    public static final CreativeModeTab TAB = new CreativeModeTab(MOD_ID) {
        @Override
        public ItemStack makeIcon() {
            return new ItemStack(AmmoItems.BLANK_MOLD.get());
        }

        @Override
        public void fillItemList(NonNullList<ItemStack> items) {
            AmmoItems.fillCreativeTab(items);
        }
    };
    public static final CreateRegistrate REGISTRATE = CreateRegistrate.create(MOD_ID)
            .creativeModeTab(() -> TAB);

    public AmmoCraft() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        REGISTRATE.registerEventListeners(bus);
        AmmoItems.register();
        AmmoRecipes.register(bus);
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MOD_ID, path);
    }
}
