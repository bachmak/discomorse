(() => {
  const stage = document.getElementById("stage");
  const world = PRES.svg.group(stage, "world");

  PRES.camera = new PRES.Camera(stage);

  const layers = [
    PRES.sceneTitle(world),
    ...PRES.sceneAbstract(world),
    ...PRES.sceneGraph(world),
    ...PRES.sceneSystem(world),
  ];
  const detailWorld = PRES.svg.group(world, "lvl-deep");
  PRES.details.build(detailWorld);

  PRES.deck = new PRES.Deck(PRES.camera, layers);
  PRES.deck.start();
  new PRES.Controls(PRES.deck);
})();
