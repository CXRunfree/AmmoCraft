package cn.crtlprototypestudios.ammocraft.compat.jei;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Vector3f;
import mezz.jei.api.ingredients.IIngredientRenderer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiComponent;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

import java.util.List;

/** Draw the mold at the center of AnimatedMixer's south-facing basin side. */
public class BasinMoldRenderer implements IIngredientRenderer<ItemStack> {
    private final ResourceLocation texture;

    public BasinMoldRenderer(String caliber) {
        texture = new ResourceLocation("ammocraft", "textures/item/ammo/molds/" + caliber + ".png");
    }

    @Override
    public void render(PoseStack pose, ItemStack ingredient) {
        pose.pushPose();
        // Undo the JEI slot offset to reach AnimatedMixer's origin. Draw above
        // its block depth so the item cannot be hidden by the basin model.
        pose.translate(-11, -22, 300);
        pose.mulPose(Vector3f.XP.rotationDegrees(-15.5f));
        pose.mulPose(Vector3f.YP.rotationDegrees(22.5f));
        pose.scale(23, 23, 23);
        // Basin is at y=1.65. Center the plate at (8, 8, 15.75) voxels;
        // GUI block rendering flips model Y, hence 1.65 - 8/16 here.
        pose.translate(8 / 16.0, 1.65 - 8 / 16.0, 15.75 / 16.0);
        // A half-block plate, centered on the side, using the original 64px art.
        pose.scale(0.5f / 64, 0.5f / 64, 0.5f / 64);
        RenderSystem.setShader(GameRenderer::getPositionTexShader);
        RenderSystem.setShaderColor(1, 1, 1, 1);
        RenderSystem.setShaderTexture(0, texture);
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        GuiComponent.blit(pose, -32, -32, 0, 0, 64, 64, 64, 64);
        pose.popPose();
    }

    @Override
    public List<Component> getTooltip(ItemStack ingredient, TooltipFlag flag) {
        return ingredient.getTooltipLines(Minecraft.getInstance().player, flag);
    }
}
