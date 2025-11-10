# Linux D-BUS BLE Tool for Programming IR Buttons on TLSR827x Remotes
## (Google G10, Homatics B21, etc.)
Based on [Genius1237/g10-ir](https://github.com/Genius1237/g10-ir)

You need to pair remote with you linux (press BACK + HOME on the remote) and pair remote via bluetoothctl. Replace MAC to your remote MAC   
```
bluetoothctl
scan on
# (press BACK + HOME on the remote)
# wait for you remote E8:DF:24:50:C1:E4
pair E8:DF:24:50:C1:E4
trust E8:DF:24:50:C1:E4
connect E8:DF:24:50:C1:E4
```
Install dbus python library ```pip install dbus-next```   
Run script ```/usr/bin/python3 /usr/local/bin/g10-ir-linux.py E8:DF:24:50:C1:E4```   

This script uses d-bus, which allows the remote to keep BT connection after programming.   

I have a Sharp TV LC-32DH500E so [This sharp codes working for my TV](https://www.remotecentral.com/cgi-bin/codes/sharp/lc-30hv2u/)   

[The IR code format for G10 is described in this post on 4pda](https://4pda.to/forum/index.php?showtopic=400717&view=findpost&p=140006470) Thanks [bnister](https://4pda.to/forum/index.php?showuser=1571790)   

Power button code   
```0000 006c 0000 0020 000a 0046 000a 001e 000a 001e 000a 001e 000a 001e 000a 001e 000a 0046 000a 0046 000a 001e 000a 0046 000a 001e 000a 001e 000a 001e 000a 0046 000a 001e 000a 06d7 000a 0046 000a 001e 000a 001e 000a 001e 000a 001e 000a 0046 000a 001e 000a 001e 000a 0046 000a 001e 000a 0046 000a 0046 000a 0046 000a 001e 000a 0046 000a 06d7```

change ```0000006c00000020``` to ```0221017c0020123c```

My power button code modified   ```0221017c0020123c000a0046000a001e000a001e000a001e000a001e000a001e000a0046000a0046000a001e000a0046000a001e000a001e000a001e000a0046000a001e000a06d7000a0046000a001e000a001e000a001e000a001e000a0046000a001e000a001e000a0046000a001e000a0046000a0046000a0046000a001e000a0046000a06d7```   

If you don't want to program the button, just leave ```00``` instead of the IR code.

> [!NOTE]
> The remote deletes the IR codes after each pairing, so you need to programming remote each paring.   
> 1. Place python script into ```/usr/local/bin/g10-ir-linux.py```   
> 2. Create file ```/etc/udev/rules.d/99-b21.rules```   
> ```ACTION=="add" SUBSYSTEM=="input", ATTR{name}=="B21 Keyboard", RUN+="/usr/bin/python3 /usr/local/bin/g10-ir-linux.py E8:DF:24:50:C1:E4"```   
> 3. Change "B21 Keyboard" to you remote name and MAC to you remote MAC, you can see name in dmesg when you reconnect remote   
> 4. Reload udev ```udevadm control --reload```

**References**
> [Other IR codes for devices on remotecentral.com](https://www.remotecentral.com/cgi-bin/codes/)   
> https://fcc.report/FCC-ID/OZ5C009/5122343.pdf  
> https://manuals.plus/ohsung-electronics/c009-rf-remote-control-unit-manual  
> https://android.googlesource.com/platform/hardware/telink/atv/refDesignRcu

![Homatics B21](/assets/images/homatics_b21.jpg)
