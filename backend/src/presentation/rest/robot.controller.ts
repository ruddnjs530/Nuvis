import { Controller, Get, Post, Body, Param } from '@nestjs/common';

/**
 * Controller for the presentation layer.
 * Receives REST API calls and maps them to Application Use Cases.
 */
@Controller('api/robots')
export class RobotController {
  
  // constructor(private readonly robotAppService: IRobotAppService) {}

  @Post(':id/clean')
  startCleaning(@Param('id') robotId: string, @Body() data: any) {
    return {
      success: true,
      message: `Start cleaning command received for robot ${robotId} via Presentation layer.`,
    };
  }
}
