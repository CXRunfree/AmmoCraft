package cn.crtlprototypestudios.ammocraft.recipe;

import cn.crtlprototypestudios.ammocraft.registry.AmmoRecipes;
import com.simibubi.create.content.contraptions.components.mixer.MixingRecipe;
import com.simibubi.create.content.contraptions.processing.ProcessingRecipeBuilder;
import net.minecraft.world.item.crafting.RecipeSerializer;

public class AmmoBlankMixingRecipe extends MixingRecipe {
    public AmmoBlankMixingRecipe(ProcessingRecipeBuilder.ProcessingRecipeParams params) {
        super(params);
    }

    @Override
    protected int getMaxInputCount() {
        // Metal and raw-powder batches consume repeated ingredients from stacked basin slots.
        return 160;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return AmmoRecipes.AMMO_MIXING.get();
    }
}
