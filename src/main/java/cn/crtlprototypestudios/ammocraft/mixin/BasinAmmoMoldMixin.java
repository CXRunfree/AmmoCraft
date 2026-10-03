package cn.crtlprototypestudios.ammocraft.mixin;

import cn.crtlprototypestudios.ammocraft.registry.AmmoItems;
import cn.crtlprototypestudios.ammocraft.item.AmmoMoldItem;
import cn.crtlprototypestudios.ammocraft.item.AmmoCasingItem;
import cn.crtlprototypestudios.ammocraft.recipe.CasingOutputAccess;
import com.simibubi.create.content.contraptions.processing.BasinRecipe;
import com.simibubi.create.content.contraptions.processing.BasinTileEntity;
import com.simibubi.create.foundation.tileEntity.behaviour.filtering.FilteringBehaviour;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(BasinRecipe.class)
public class BasinAmmoMoldMixin {
    @Redirect(method = "match", at = @At(value = "INVOKE", target =
            "Lcom/simibubi/create/foundation/tileEntity/behaviour/filtering/FilteringBehaviour;test(Lnet/minecraft/world/item/ItemStack;)Z"), remap = false)
    private static boolean ammocraft$selectMold(FilteringBehaviour filter, ItemStack output,
                                         BasinTileEntity basin, Recipe<?> recipe) {
        if (output.getItem() instanceof AmmoCasingItem)
            return ammocraft$matchesMold(basin, recipe);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS)
            if (output.is(caliber.powder.get()))
                return filter.getFilter().is(caliber.powder.get());
        return filter.test(output);
    }

    @Inject(method = "apply(Lcom/simibubi/create/content/contraptions/processing/BasinTileEntity;Lnet/minecraft/world/item/crafting/Recipe;Z)Z",
            at = @At("HEAD"), cancellable = true, remap = false)
    private static void ammocraft$requireMold(BasinTileEntity basin, Recipe<?> recipe, boolean simulate,
                                         CallbackInfoReturnable<Boolean> cir) {
        if (recipe.getResultItem().getItem() instanceof AmmoCasingItem
                && !((CasingOutputAccess) basin).ammocraft$canFitCasingBatch(recipe.getResultItem())) {
            cir.setReturnValue(false);
            return;
        }
        if (recipe.getResultItem().getItem() instanceof AmmoCasingItem && !ammocraft$matchesMold(basin, recipe))
            cir.setReturnValue(false);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS)
            if (recipe.getResultItem().is(caliber.powder.get())
                    && (basin.getFilter() == null || !basin.getFilter().getFilter().is(caliber.powder.get())))
                cir.setReturnValue(false);
    }

    @Unique
    private static boolean ammocraft$matchesMold(BasinTileEntity basin, Recipe<?> recipe) {
        FilteringBehaviour filter = basin.getFilter();
        return filter != null && filter.getFilter().getItem() instanceof AmmoMoldItem mold
                && recipe.getId().equals(mold.getMixingRecipeId());
    }
}
