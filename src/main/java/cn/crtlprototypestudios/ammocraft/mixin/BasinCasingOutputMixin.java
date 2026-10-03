package cn.crtlprototypestudios.ammocraft.mixin;

import cn.crtlprototypestudios.ammocraft.item.AmmoCasingItem;
import com.simibubi.create.content.contraptions.processing.BasinBlock;
import com.simibubi.create.content.contraptions.processing.BasinTileEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.items.CapabilityItemHandler;
import net.minecraftforge.items.ItemHandlerHelper;
import com.simibubi.create.foundation.tileEntity.TileEntityBehaviour;
import com.simibubi.create.foundation.tileEntity.behaviour.filtering.FilteringBehaviour;
import com.simibubi.create.foundation.tileEntity.behaviour.inventory.InvManipulationBehaviour;
import net.minecraftforge.items.IItemHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.List;

@Mixin(BasinTileEntity.class)
public abstract class BasinCasingOutputMixin {
    @Shadow(remap = false)
    protected List<ItemStack> spoutputBuffer;

    @Inject(method = "tick", at = @At("HEAD"), remap = false)
    private void ammocraft$recoverBufferedCasings(CallbackInfo ci) {
        BasinTileEntity basin = (BasinTileEntity) (Object) this;
        if (basin.getLevel() == null || basin.getLevel().isClientSide) return;
        var inventory = basin.getOutputInventory();
        boolean changed = false;
        var iterator = spoutputBuffer.iterator();
        while (iterator.hasNext()) {
            ItemStack buffered = iterator.next();
            if (!(buffered.getItem() instanceof AmmoCasingItem)) continue;
            if (buffered.getCount() <= buffered.getMaxStackSize()
                    && ammocraft$receiverAccepts(basin, buffered)) continue;
            // The spout buffer is invisible to hoppers. Recover it into output
            // slots without BasinInventory's same-item insertion restriction.
            for (int slot = 0; slot < inventory.getSlots() && !buffered.isEmpty(); slot++) {
                ItemStack stored = inventory.getStackInSlot(slot);
                if (!stored.isEmpty() && !ItemHandlerHelper.canItemStacksStack(stored, buffered)) continue;
                int room = Math.min(inventory.getSlotLimit(slot), buffered.getMaxStackSize()) - stored.getCount();
                if (room <= 0) continue;
                int amount = Math.min(room, buffered.getCount());
                ItemStack merged = buffered.copy();
                merged.setCount(stored.getCount() + amount);
                inventory.setStackInSlot(slot, merged);
                buffered.shrink(amount);
                changed = true;
            }
            if (buffered.isEmpty()) iterator.remove();
        }
        if (changed) {
            basin.notifyChangeOfContents();
            basin.sendData();
        }
    }

    @Inject(method = "tick", at = @At("RETURN"), remap = false)
    private void ammocraft$retryCasingOutput(CallbackInfo ci) {
        BasinTileEntity basin = (BasinTileEntity) (Object) this;
        if (basin.getLevel() == null || basin.getLevel().isClientSide || !spoutputBuffer.isEmpty()) return;
        if (!basin.getBlockState().hasProperty(BasinBlock.FACING)
                || !basin.getBlockState().getValue(BasinBlock.FACING).getAxis().isHorizontal()) return;
        // Leave blocked outputs accessible to extraction instead of returning
        // them to the hidden spout buffer on every tick.
        var inventory = basin.getOutputInventory();
        for (int slot = 0; slot < inventory.getSlots(); slot++) {
            ItemStack stored = inventory.getStackInSlot(slot);
            if (stored.isEmpty() || !(stored.getItem() instanceof AmmoCasingItem)) continue;
            int amount = Math.min(stored.getCount(), stored.getMaxStackSize());
            ItemStack transfer = stored.copy();
            transfer.setCount(amount);
            if (!ammocraft$receiverAccepts(basin, transfer)) continue;
            if (!basin.acceptOutputs(List.of(transfer), List.of(), true)) return;
            if (!basin.acceptOutputs(List.of(transfer), List.of(), false)) return;
            // Output inventories can prohibit extraction by automation. Mutate
            // only this owned output slot, never the basin's ingredient slots.
            ItemStack remainder = stored.copy();
            remainder.shrink(amount);
            inventory.setStackInSlot(slot, remainder.isEmpty() ? ItemStack.EMPTY : remainder);
            basin.notifyChangeOfContents();
            basin.sendData();
            return;
        }
    }

    @Unique
    private boolean ammocraft$receiverAccepts(BasinTileEntity basin, ItemStack transfer) {
        if (!basin.getBlockState().hasProperty(BasinBlock.FACING)) return false;
        var direction = basin.getBlockState().getValue(BasinBlock.FACING);
        if (!direction.getAxis().isHorizontal()) return false;
        var receiverPos = basin.getBlockPos().below().relative(direction);
        var receiver = basin.getLevel().getBlockEntity(receiverPos);
        if (receiver == null) return false;
        InvManipulationBehaviour manipulation = TileEntityBehaviour.get(basin.getLevel(), receiverPos,
                InvManipulationBehaviour.TYPE);
        IItemHandler fallback = manipulation == null ? null : manipulation.getInventory();
        var target = receiver.getCapability(CapabilityItemHandler.ITEM_HANDLER_CAPABILITY,
                direction.getOpposite()).orElse(fallback);
        FilteringBehaviour filter = TileEntityBehaviour.get(basin.getLevel(), receiverPos, FilteringBehaviour.TYPE);
        return target != null && (filter == null || filter.test(transfer))
                && ItemHandlerHelper.insertItemStacked(target, transfer.copy(), true).isEmpty();
    }
}
