# AmmoCraft v1.0.0

基于 Create 的 TaCZ 弹药自动化模组，独立模组 ID：`ammocraft`。

## 环境

- Minecraft 1.18.2 / Forge 40.2.21
- Create 0.5.0.i / Flywheel 0.6.8.a
- TaCZ 1.1.4+ 提供最终弹药；不内嵌 TaCZ 或 Registrate
- Java 17；素材工具使用 Python 3 和 Pillow

## 流水线

1. 动力合成器用 2×2 排列的四个黑曜石制作一个空白模板。
2. 机械手持对应 TaCZ 弹药刻制模板，样品保留。
3. 模板放入工作盆过滤槽，搅拌铜/铁得到独立弹壳 `ammocraft:casing_<口径>`。
4. 机械手持拆解钳拆卸一发弹药，得到对应口径火药，钳子保留并产生金属碎屑粒子。
5. 对应火药放入工作盆过滤槽，用普通火药及指定添加物搅拌生产口径火药。
6. 机械手给弹壳装药，转换为带装配进度的 `ammocraft:incomplete_<口径>`，随后动力压制器压成一发 TaCZ 弹药。12g 装药后额外消耗一铁粒。

工作盆容量沿用 Create 原版逻辑，不额外限制弹壳总量；内部输出槽中滞留的弹壳会通过 Create 原版输出缓冲重试输出。模板筛选和口径火药过滤仍由配方筛选 Mixin 实现；所有独立弹壳物品的堆叠上限统一为 60。

包含 19 种口径、独立小批次、独立青金石粉、多发模板、右上 45° 的 RPG 模板，以及边缘相互重叠的弹药素材。半成品使用最新制作的素材。

## 构建与验证

```powershell
.\gradlew.bat build --console=plain
.\gradlew.bat runGameTestServer --console=plain
python tools/verify_ammo_artifact.py
```

默认产物：`build/libs/AmmoCraft-1.0.0.jar`。

```powershell
python tools/generate_recipes.py
python tools/generate_assets.py
python tools/verify_ammo_artifact.py --resources
```

素材生成用到的少量 TaCZ / Minecraft 参考素材放在 `tools/reference/`，不随 JAR 打包；不需要原工程路径。Gradle 首次构建需要下载依赖，缓存齐全后可加 `--offline`。

## 迁移说明

这是新的独立模组，物品与配方均使用 `ammocraft:` 命名空间。原 PRMA 工程保留，旧存档的 `prma:` 物品不会自动转换。

项目只包含弹药流水线相关内容、素材生成工具和测试。新模组发布与版本号从 v1.0.0 开始。
