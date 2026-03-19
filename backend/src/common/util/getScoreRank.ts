export function getScoreRank(score: number): string {
  let scoreRank: string = '';
  if (score >= 9900000) {
    scoreRank = 's';
  } else if (score >= 9800000) {
    scoreRank = 'AAA+';
  } else if (score >= 9700000) {
    scoreRank = 'AAA';
  } else if (score >= 9500000) {
    scoreRank = 'AA+';
  } else if (score >= 9300000) {
    scoreRank = 'AA';
  } else if (score >= 9000000) {
    scoreRank = 'A+';
  } else if (score >= 8700000) {
    scoreRank = 'A';
  } else if (score >= 7500000) {
    scoreRank = 'B';
  } else if (score >= 6500000) {
    scoreRank = 'C';
  } else {
    scoreRank = 'D';
  }
  return scoreRank;
}
