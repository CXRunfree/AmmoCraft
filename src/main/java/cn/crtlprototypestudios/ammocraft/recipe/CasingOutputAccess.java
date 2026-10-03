package cn.crtlprototypestudios.ammocraft.recipe;

import net.minecraft.world.item.ItemStack;

/** Basin output state used to apply backpressure to casing manufacturing. */
public interface CasingOutputAccess {
    int MAX_CASINGS_PER_TYPE = 60;

    boolean ammocraft$canFitCasingBatch(ItemStack batch);
}
