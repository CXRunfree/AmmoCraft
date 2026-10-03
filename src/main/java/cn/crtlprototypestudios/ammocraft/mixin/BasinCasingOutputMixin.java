package cn.crtlprototypestudios.ammocraft.mixin;

import cn.crtlprototypestudios.ammocraft.item.AmmoCasingItem;
import com.simibubi.create.content.contraptions.processing.BasinBlock;
import com.simibubi.create.content.contraptions.processing.BasinTileEntity;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.List;

@Mixin(BasinTileEntity.class)
public abstract class BasinCasingOutputMixin {
    @Shadow(remap = false)
    protected List<ItemStack> spoutputBuffer;

    @Inject(method = "tick", at = @At("TAIL"), remap = false)
    private void ammocraft$retryCasingOutput(CallbackInfo ci) {
        BasinTileEntity basin = (BasinTileEntity) (Object) this;
        if (basin.getLevel() == null || basin.getLevel().isClientSide || !spoutputBuffer.isEmpty()) return;
        if (!basin.getBlockState().hasProperty(BasinBlock.FACING)
                || !basin.getBlockState().getValue(BasinBlock.FACING).getAxis().isHorizontal()) return;
        // Create transfers its internal output slots only when the spout changes
        // direction. Retry stranded casings through its normal overflow buffer.
        // Move one legal stack at a time and only remove it after queuing succeeds.
        var inventory = basin.getOutputInventory();
        for (int slot = 0; slot < inventory.getSlots(); slot++) {
            ItemStack stored = inventory.getStackInSlot(slot);
            if (!(stored.getItem() instanceof AmmoCasingItem)) continue;
            int amount = Math.min(stored.getCount(), stored.getMaxStackSize());
            ItemStack transfer = stored.copy();
            transfer.setCount(amount);
            if (!basin.acceptOutputs(List.of(transfer), List.of(), true)) return;
            if (!basin.acceptOutputs(List.of(transfer), List.of(), false)) return;
            // Output inventories can prohibit extraction by automation. Mutate
            // only this owned output slot, never the basin's ingredient slots.
            ItemStack remainder = stored.copy();
            remainder.shrink(amount);
            inventory.setStackInSlot(slot, remainder);
            basin.notifyChangeOfContents();
            basin.sendData();
            return;
        }
    }
}
