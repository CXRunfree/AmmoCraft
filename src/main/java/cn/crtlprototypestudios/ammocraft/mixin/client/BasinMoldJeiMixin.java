package cn.crtlprototypestudios.ammocraft.mixin.client;

import cn.crtlprototypestudios.ammocraft.recipe.AmmoBlankMixingRecipe;
import cn.crtlprototypestudios.ammocraft.compat.jei.BasinMoldRenderer;
import cn.crtlprototypestudios.ammocraft.registry.AmmoItems;
import com.simibubi.create.compat.jei.category.CreateRecipeCategory;
import com.simibubi.create.content.contraptions.processing.BasinRecipe;
import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.constants.VanillaTypes;
import net.minecraft.network.chat.TranslatableComponent;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "com.simibubi.create.compat.jei.category.BasinCategory", remap = false)
public abstract class BasinMoldJeiMixin {
    @Inject(method = "setRecipe(Lmezz/jei/api/gui/builder/IRecipeLayoutBuilder;Lcom/simibubi/create/content/contraptions/processing/BasinRecipe;Lmezz/jei/api/recipe/IFocusGroup;)V",
            at = @At("TAIL"), remap = false)
    private void ammocraft$showRequiredMold(IRecipeLayoutBuilder builder, BasinRecipe recipe,
                                           IFocusGroup focuses, CallbackInfo ci) {
        if (!(recipe instanceof AmmoBlankMixingRecipe)) return;
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            if (!recipe.getId().equals(caliber.mold.get().getMixingRecipeId())) continue;
            // Center the 16px hover slot on the plate at (8, 8, 15.75) voxels
            // on AnimatedMixer's south face, six GUI pixels below the filter.
            int x = ((CreateRecipeCategory<?>) (Object) this).getBackground().getWidth() / 2 + 14;
            builder.addSlot(RecipeIngredientRole.CATALYST, x, 56)
                    .setSlotName("ammocraft.mold_filter")
                    .setCustomRenderer(VanillaTypes.ITEM_STACK, new BasinMoldRenderer(caliber.id))
                    .addTooltipCallback((slot, tooltip) ->
                            tooltip.add(new TranslatableComponent("tooltip.ammocraft.ammo_mold")))
                    .addItemStack(new ItemStack(caliber.mold.get()));
            return;
        }
    }
}
