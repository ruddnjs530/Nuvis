using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class RobotUdpBridge : MonoBehaviour
{
    [Header("ROS Bridge Endpoint")]
    public string rosHost = "127.0.0.1";
    public int rosCommandPort = 9002;     // Unity -> ROS
    public int unityListenPort = 9001;    // ROS -> Unity

    [Header("Debug")]
    public bool printIncoming = true;

    private UdpClient _sendClient;
    private UdpClient _recvClient;
    private Thread _recvThread;
    private volatile bool _running;
    private readonly ConcurrentQueue<string> _incomingQueue = new ConcurrentQueue<string>();

    public string LastMessage;

    void Start()
    {
        _sendClient = new UdpClient();
        _recvClient = new UdpClient(unityListenPort);
        _running = true;
        _recvThread = new Thread(ReceiveLoop);
        _recvThread.IsBackground = true;
        _recvThread.Start();
        Debug.Log($"[RobotUdpBridge] started (send -> {rosHost}:{rosCommandPort}, recv <- *:{unityListenPort})");
    }

    void Update()
    {
        while (_incomingQueue.TryDequeue(out var msg))
        {
            LastMessage = msg;
            if (printIncoming)
            {
                Debug.Log($"[RobotUdpBridge] RX: {msg}");
            }
        }
    }

    void OnDestroy()
    {
        _running = false;
        try { _recvClient?.Close(); } catch { }
        try { _sendClient?.Close(); } catch { }
        try { _recvThread?.Join(200); } catch { }
    }

    private void ReceiveLoop()
    {
        IPEndPoint endpoint = new IPEndPoint(IPAddress.Any, unityListenPort);
        while (_running)
        {
            try
            {
                byte[] bytes = _recvClient.Receive(ref endpoint);
                string text = Encoding.UTF8.GetString(bytes);
                _incomingQueue.Enqueue(text);
            }
            catch (SocketException)
            {
                Thread.Sleep(10);
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch (Exception ex)
            {
                _incomingQueue.Enqueue($"{{\"type\":\"unity_error\",\"data\":{{\"message\":\"{ex.Message}\"}}}}");
                Thread.Sleep(50);
            }
        }
    }

    public void SendRawJson(string json)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(json);
        _sendClient.Send(bytes, bytes.Length, rosHost, rosCommandPort);
        Debug.Log($"[RobotUdpBridge] TX: {json}");
    }

    [ContextMenu("Ping")]
    public void SendPing()
    {
        SendRawJson("{\"type\":\"ping\"}");
    }

    [ContextMenu("Execute Sample Task")]
    public void SendExecuteTaskSample()
    {
        string commandId = $"unity-cmd-{Guid.NewGuid():N}";
        string taskId = $"unity-task-{Guid.NewGuid():N}";
        string json =
            "{" +
            "\"type\":\"execute_task\"," +
            "\"data\":{" +
                $"\"command_id\":\"{commandId}\"," +
                $"\"task_id\":\"{taskId}\"," +
                "\"task_type\":0," +
                "\"target_zone\":\"living_room\"," +
                "\"module_type\":1," +
                "\"module_power\":true," +
                "\"module_level\":2," +
                "\"max_exec_sec\":120" +
            "}" +
            "}";
        SendRawJson(json);
    }

    [ContextMenu("Emergency Stop")]
    public void SendEmergencyStop()
    {
        string commandId = $"unity-estop-{Guid.NewGuid():N}";
        string json =
            "{" +
            "\"type\":\"emergency_stop\"," +
            "\"data\":{" +
                $"\"command_id\":\"{commandId}\"," +
                "\"reason\":\"unity_manual_estop\"" +
            "}" +
            "}";
        SendRawJson(json);
    }
}
