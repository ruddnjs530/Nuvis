import { Injectable, Logger } from '@nestjs/common';

/**
 * Service for the infrastructure layer.
 * Implements outward-facing dependencies like ROS2, Database, External APIs.
 */
@Injectable()
export class Ros2BridgeAdapter {
  private readonly logger = new Logger(Ros2BridgeAdapter.name);

  constructor() {
    this.logger.log('Initializing ROS2 Bridge Client in Infrastructure layer...');
  }

  public publishCommand(topic: string, message: any) {
    this.logger.log(`Publishing to ${topic}: ${JSON.stringify(message)}`);
  }
}
