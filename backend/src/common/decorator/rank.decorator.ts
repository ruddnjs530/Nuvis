import { SetMetadata } from '@nestjs/common';

export const Rank = (rankIdx: number) => SetMetadata('rankIdx', rankIdx);
