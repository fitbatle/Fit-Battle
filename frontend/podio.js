function ordenarVagasPodio(dados) {
  const primeiro = dados[0];
  const segundo = dados[1];
  const terceiro = dados[2];
  if (!primeiro) return [];
  if (!segundo) return [primeiro];
  if (!terceiro) return [segundo, primeiro];
  return [segundo, primeiro, terceiro];
}
