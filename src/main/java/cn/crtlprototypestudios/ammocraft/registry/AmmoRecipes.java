package cn.crtlprototypestudios.ammocraft.registry;

import cn.crtlprototypestudios.ammocraft.AmmoCraft;
import cn.crtlprototypestudios.ammocraft.recipe.AmmoBlankMixingRecipe;
import com.simibubi.create.content.contraptions.processing.ProcessingRecipeSerializer;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public class AmmoRecipes {
    public static final DeferredRegister<RecipeSerializer<?>> SERIALIZERS =
            DeferredRegister.create(ForgeRegistries.RECIPE_SERIALIZERS, AmmoCraft.MOD_ID);
    public static final RegistryObject<RecipeSerializer<AmmoBlankMixingRecipe>> AMMO_MIXING =
            SERIALIZERS.register("ammo_mixing", () -> new ProcessingRecipeSerializer<>(AmmoBlankMixingRecipe::new));

    public static void register(IEventBus bus) {
        SERIALIZERS.register(bus);
    }
}
